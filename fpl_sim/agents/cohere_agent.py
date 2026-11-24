from __future__ import annotations

import json
import os
import time
from typing import Any

from dotenv import load_dotenv

from fpl_sim.tools.context import ToolContext
from fpl_sim.tools.schemas import cohere_tools, dispatch
from fpl_sim.tracking.tracing import set_outputs, span

_RATE_LIMIT_ATTEMPTS = 8
_RATE_LIMIT_WAIT_S = 20.0
_RATE_LIMIT_WAIT_MAX_S = 60.0


class CohereAgent:
    def __init__(
        self,
        model: str,
        temperature: float = 0.3,
        seed: int | None = 42,
        max_tool_calls: int = 40,
        max_turns: int = 40,
        tool_names: list[str] | None = None,
    ) -> None:
        load_dotenv()
        api_key = os.environ.get("COHERE_API_KEY")
        if not api_key:
            raise RuntimeError("COHERE_API_KEY must be set")
        try:
            from cohere import ClientV2
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("cohere package is required") from exc
        self.client = ClientV2(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.seed = seed
        self.max_tool_calls = max_tool_calls
        self.max_turns = max_turns
        self.tool_names = tool_names
        self.tools = cohere_tools(tool_names)

    def run(
        self,
        system: str,
        user: str,
        ctx: ToolContext,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        meta = metadata or {}
        with span(
            "cohere_agent",
            span_type="AGENT",
            inputs={"user": user, "system": system},
            attributes={"model": self.model, **meta},
        ) as agent_span:
            result = self._run_loop(system, user, ctx)
            set_outputs(
                agent_span,
                {
                    "finalized": result["finalized"],
                    "tool_calls": ctx.stats.tool_calls,
                    "invalid_actions": ctx.stats.invalid_actions,
                    "text": result.get("text") or "",
                },
            )
            return result

    def _run_loop(self, system: str, user: str, ctx: ToolContext) -> dict[str, Any]:
        messages: list[Any] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_text = ""
        started = time.perf_counter()
        for turn in range(self.max_turns):
            ctx.stats.turns = turn + 1
            if ctx.stats.tool_calls >= self.max_tool_calls and not ctx.finalized:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You are at the tool-call budget. Lock now using the evidence you have. "
                            "Call submit_lineup if the squad and lineup are valid."
                        ),
                    }
                )
            elif turn >= self.max_turns - 2 and not ctx.finalized:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You are near the turn limit. Submit any missing squad/lineup fixes now "
                            "and call submit_lineup if they are valid to lock this Gameweek."
                        ),
                    }
                )
            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "tools": self.tools,
                "temperature": self.temperature,
            }
            if self.seed is not None:
                kwargs["seed"] = self.seed
            with span(
                "cohere.chat",
                span_type="LLM",
                inputs={"turn": turn + 1, "model": self.model},
                attributes={"turn": turn + 1},
            ) as llm_span:
                response = self._chat(kwargs)
                self._add_usage(ctx, response)
                message = response.message
                tool_calls = _tool_calls(message)
                text = _message_text(message)
                set_outputs(
                    llm_span,
                    {
                        "text": text,
                        "tool_calls": [c["name"] for c in tool_calls],
                    },
                )
            if text:
                last_text = text
            messages.append(message)
            if not tool_calls:
                if ctx.finalized:
                    break
                messages.append(
                    {
                        "role": "user",
                        "content": "You must take actions through tools. Call submit_lineup to lock when the squad and lineup are valid.",
                    }
                )
                continue
            for call in tool_calls:
                name = call["name"]
                args = call["arguments"]
                with span(
                    f"tool.{name}",
                    span_type="TOOL",
                    inputs={"arguments": args},
                    attributes={"tool_name": name},
                ) as tool_span:
                    if ctx.stats.tool_calls >= self.max_tool_calls and name != "submit_lineup":
                        result = {
                            "accepted": False,
                            "errors": ["Tool-call budget reached. Call submit_lineup to lock."],
                        }
                    else:
                        result = dispatch(ctx, name, args)
                    set_outputs(tool_span, {"result": result})
                messages.append(_tool_result_message(call["id"], result))
                if ctx.finalized:
                    break
            if ctx.finalized:
                break
        ctx.stats.latency_ms = (time.perf_counter() - started) * 1000
        return {"text": last_text, "finalized": ctx.finalized, "stats": ctx.stats}

    def _chat(self, kwargs: dict[str, Any]) -> Any:
        wait = _RATE_LIMIT_WAIT_S
        last_exc: BaseException | None = None
        for attempt in range(1, _RATE_LIMIT_ATTEMPTS + 1):
            try:
                return self.client.chat(**kwargs)
            except Exception as exc:  # noqa: BLE001
                if not _is_rate_limit(exc):
                    raise
                last_exc = exc
                if attempt >= _RATE_LIMIT_ATTEMPTS:
                    break
                pause = _retry_after_seconds(exc) or wait
                print(
                    f"Cohere per-minute limit (429). Waiting {pause:.0f}s "
                    f"then retrying chat ({attempt}/{_RATE_LIMIT_ATTEMPTS})."
                )
                time.sleep(pause)
                wait = min(wait * 1.5, _RATE_LIMIT_WAIT_MAX_S)
        assert last_exc is not None
        raise last_exc

    def _add_usage(self, ctx: ToolContext, response: Any) -> None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        billed = getattr(usage, "billed_units", None) or getattr(usage, "tokens", None)
        if billed is None:
            return
        ctx.stats.input_tokens += int(getattr(billed, "input_tokens", 0) or 0)
        ctx.stats.output_tokens += int(getattr(billed, "output_tokens", 0) or 0)


def _is_rate_limit(exc: BaseException) -> bool:
    if int(getattr(exc, "status_code", 0) or 0) == 429:
        return True
    return type(exc).__name__ == "TooManyRequestsError"


def _retry_after_seconds(exc: BaseException) -> float | None:
    headers = getattr(exc, "headers", None) or {}
    if not isinstance(headers, dict):
        return None
    raw = headers.get("retry-after") or headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return max(1.0, float(raw))
    except (TypeError, ValueError):
        return None


def _tool_calls(message: Any) -> list[dict[str, Any]]:
    raw = getattr(message, "tool_calls", None) or []
    parsed: list[dict[str, Any]] = []
    for i, call in enumerate(raw):
        fn = getattr(call, "function", None)
        name = getattr(fn, "name", None) if fn is not None else getattr(call, "name", None)
        args = getattr(fn, "arguments", None) if fn is not None else getattr(call, "arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args) if args else {}
            except json.JSONDecodeError:
                args = {}
        parsed.append(
            {
                "id": getattr(call, "id", None) or f"call_{i}",
                "name": name,
                "arguments": args or {},
            }
        )
    return parsed


def _tool_result_message(tool_call_id: str, result: Any) -> dict[str, Any]:
    payload = result if isinstance(result, (dict, list, str, int, float, bool)) else str(result)
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": [
            {
                "type": "document",
                "document": {"data": json.dumps(payload, default=str)},
            }
        ],
    }


def _message_text(message: Any) -> str:
    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content
    if not content:
        return ""
    parts = []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)
