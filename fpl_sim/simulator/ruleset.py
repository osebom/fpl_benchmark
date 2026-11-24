from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from fpl_sim.paths import repo_root


@dataclass(frozen=True)
class Ruleset:
    raw: dict[str, Any]

    @classmethod
    def load(cls, path: str | Path | None = None) -> Ruleset:
        resolved = Path(path) if path else repo_root() / "configs" / "rules" / "fpl_2025_26.yaml"
        if not resolved.is_absolute():
            resolved = repo_root() / resolved
        with resolved.open() as fh:
            return cls(yaml.safe_load(fh))

    @property
    def initial_budget_tenths(self) -> int:
        return int(self.raw["budget"]["initial_tenths"])

    @property
    def max_per_club(self) -> int:
        return int(self.raw["squad"]["max_per_club"])

    @property
    def squad_positions(self) -> dict[str, int]:
        return {k: int(v) for k, v in self.raw["squad"]["positions"].items()}

    @property
    def max_free_transfers(self) -> int:
        return int(self.raw["transfers"]["max_free_transfers"])

    @property
    def hit_cost(self) -> int:
        return int(self.raw["transfers"]["hit_cost"])

    @property
    def weekly_accrual(self) -> int:
        return int(self.raw["transfers"]["weekly_accrual"])

    @property
    def gw1_free_transfers(self) -> int:
        return int(self.raw["transfers"]["gw1_free_transfers"])

    @property
    def lineup(self) -> dict[str, Any]:
        return self.raw["lineup"]

    @property
    def chip_entitlements(self) -> list[dict[str, Any]]:
        return list(self.raw["chips"]["entitlements"])

    @property
    def captain_multiplier(self) -> int:
        return int(self.raw["captaincy"]["default_multiplier"])

    @property
    def triple_captain_multiplier(self) -> int:
        return int(self.raw["captaincy"]["triple_captain_multiplier"])

    @property
    def appeared_minutes_min(self) -> int:
        return int(self.raw["captaincy"]["appeared_minutes_min"])
