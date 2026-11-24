from __future__ import annotations

from fpl_sim.simulator.ruleset import Ruleset


def active_captain(
    captain_id: int,
    vice_captain_id: int,
    minutes: dict[int, int],
    rules: Ruleset,
) -> int | None:
    threshold = rules.appeared_minutes_min
    if minutes.get(int(captain_id), 0) >= threshold:
        return int(captain_id)
    if minutes.get(int(vice_captain_id), 0) >= threshold:
        return int(vice_captain_id)
    return None


def captain_multiplier(chip_type: str | None, rules: Ruleset) -> int:
    if chip_type == "3xc":
        return rules.triple_captain_multiplier
    return rules.captain_multiplier
