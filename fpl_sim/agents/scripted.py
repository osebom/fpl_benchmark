from __future__ import annotations

from typing import Any

from fpl_sim.tools.context import ToolContext
from fpl_sim.tools.schemas import dispatch


class ScriptedAgent:
    """Deterministic agent for tests and notebook dry-runs.

    `calls` is either one script (list of (name, args)) or a queue of scripts,
    one consumed per Gameweek session.
    """

    def __init__(
        self,
        calls: list[tuple[str, dict[str, Any]]] | list[list[tuple[str, dict[str, Any]]]],
    ) -> None:
        if calls and isinstance(calls[0], tuple):
            self.queue: list[list[tuple[str, dict[str, Any]]]] = [calls]  # type: ignore[list-item]
        else:
            self.queue = list(calls)  # type: ignore[arg-type]

    def run(
        self,
        system: str,
        user: str,
        ctx: ToolContext,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last = None
        script = self.queue.pop(0) if self.queue else []
        for name, args in script:
            last = dispatch(ctx, name, args)
        return {"finalized": ctx.finalized, "stats": ctx.stats, "last": last}
