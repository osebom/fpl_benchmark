from __future__ import annotations

from contextlib import contextmanager, nullcontext
from typing import Any, Iterator

from fpl_sim.tracking.mlflow_tracker import tracing_enabled

_MAX = 4000


def _clip(value: Any) -> Any:
    text = str(value)
    if len(text) <= _MAX:
        return value
    return text[:_MAX] + "…[truncated]"


@contextmanager
def span(
    name: str,
    span_type: str | None = None,
    inputs: dict[str, Any] | None = None,
    attributes: dict[str, Any] | None = None,
) -> Iterator[Any]:
    if not tracing_enabled():
        yield None
        return
    import mlflow

    kwargs: dict[str, Any] = {"name": name}
    if span_type:
        kwargs["span_type"] = span_type
    with mlflow.start_span(**kwargs) as active:
        if inputs:
            active.set_inputs({k: _clip(v) for k, v in inputs.items()})
        if attributes:
            for key, value in attributes.items():
                if value is not None:
                    active.set_attribute(key, value)
        yield active


def set_outputs(active: Any, outputs: dict[str, Any]) -> None:
    if active is None:
        return
    active.set_outputs({k: _clip(v) for k, v in outputs.items()})


def span_trace_id(active: Any) -> str | None:
    if active is None:
        return None
    for attr in ("trace_id", "request_id"):
        value = getattr(active, attr, None)
        if value:
            return str(value)
    ctx = getattr(active, "context", None)
    if ctx is not None:
        value = getattr(ctx, "trace_id", None) or getattr(ctx, "request_id", None)
        if value:
            return str(value)
    return None


def parent_span(name: str, span_type: str = "CHAIN", **kwargs: Any):
    if not tracing_enabled():
        return nullcontext(None)
    return span(name, span_type=span_type, **kwargs)
