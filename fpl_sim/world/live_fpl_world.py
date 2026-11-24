from __future__ import annotations

from fpl_sim.world.context import WorldContext


class LiveFPLWorld:
    """Placeholder for a later live-season provider with the same tool contracts."""

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError(
            "LiveFPLWorld is not implemented. Use HistoricalCSVWorld for 2025/26."
        )


def live_world_context() -> WorldContext:
    raise NotImplementedError("Live season WorldContext is not implemented yet.")
