from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Phase = Literal["pre_deadline", "post_gameweek"]


@dataclass(frozen=True)
class WorldContext:
    season: str = "2025_26"
    current_gw: int = 1
    phase: Phase = "pre_deadline"

    def __post_init__(self) -> None:
        if not 1 <= self.current_gw <= 38:
            raise ValueError(f"current_gw must be 1-38, got {self.current_gw}")
        if self.phase not in ("pre_deadline", "post_gameweek"):
            raise ValueError(f"invalid phase: {self.phase}")

    @property
    def latest_completed_gw(self) -> int | None:
        if self.phase == "pre_deadline":
            return self.current_gw - 1 if self.current_gw > 1 else None
        return self.current_gw

    def with_phase(self, phase: Phase) -> WorldContext:
        return WorldContext(season=self.season, current_gw=self.current_gw, phase=phase)

    def next_pre_deadline(self) -> WorldContext:
        if self.current_gw >= 38:
            raise ValueError("no Gameweek after 38")
        return WorldContext(
            season=self.season,
            current_gw=self.current_gw + 1,
            phase="pre_deadline",
        )
