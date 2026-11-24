from __future__ import annotations

from collections import Counter

from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.types import PlayerView, ValidationResult


def validate_lineup(
    squad_ids: list[int],
    starters: list[int],
    bench_outfield: list[int],
    reserve_gk: int,
    captain_id: int,
    vice_captain_id: int,
    players: dict[int, PlayerView],
    rules: Ruleset,
) -> ValidationResult:
    errors: list[str] = []
    squad = [int(x) for x in squad_ids]
    start = [int(x) for x in starters]
    bench = [int(x) for x in bench_outfield]
    reserve = int(reserve_gk)
    captain = int(captain_id)
    vice = int(vice_captain_id)

    if len(start) != 11:
        errors.append(f"Starting XI must contain 11 players, got {len(start)}.")
    if len(set(start)) != len(start):
        errors.append("Starting XI contains duplicates.")
    if len(bench) != 3:
        errors.append("Bench must list exactly three outfield substitutes in order.")
    if len(set(bench)) != len(bench):
        errors.append("Bench contains duplicates.")

    all_named = start + bench + [reserve]
    if len(set(all_named)) != 15:
        errors.append("Starters, bench, and reserve GK must be 15 unique players.")
    extra = [pid for pid in all_named if pid not in set(squad)]
    if extra:
        errors.append(f"Lineup includes players who are not in the squad: {extra}.")
    missing = [pid for pid in squad if pid not in set(all_named)]
    if missing:
        errors.append(f"Squad players missing from lineup: {missing}.")

    unknown = [pid for pid in all_named if pid not in players]
    if unknown:
        errors.append(f"Unknown player ids in lineup: {unknown}.")
        return ValidationResult.fail(*errors)

    gk_starters = [pid for pid in start if players[pid].position == "GK"]
    if len(gk_starters) != 1:
        errors.append(f"Starting XI must contain exactly 1 GK, got {len(gk_starters)}.")
    if players[reserve].position != "GK":
        errors.append("Reserve must be the non-starting goalkeeper.")
    if reserve in start:
        errors.append("Reserve GK cannot also be a starter.")

    for pid in bench:
        if players[pid].position == "GK":
            errors.append("Outfield bench cannot include a goalkeeper.")

    counts = Counter(players[pid].position for pid in start)
    bounds = rules.lineup
    if counts.get("DEF", 0) < bounds["def"]["min"] or counts.get("DEF", 0) > bounds["def"]["max"]:
        errors.append(
            f"Starting XI DEF must be {bounds['def']['min']}-{bounds['def']['max']}, got {counts.get('DEF', 0)}."
        )
    if counts.get("MID", 0) < bounds["mid"]["min"] or counts.get("MID", 0) > bounds["mid"]["max"]:
        errors.append(
            f"Starting XI MID must be {bounds['mid']['min']}-{bounds['mid']['max']}, got {counts.get('MID', 0)}."
        )
    if counts.get("FWD", 0) < bounds["fwd"]["min"] or counts.get("FWD", 0) > bounds["fwd"]["max"]:
        errors.append(
            f"Starting XI FWD must be {bounds['fwd']['min']}-{bounds['fwd']['max']}, got {counts.get('FWD', 0)}."
        )

    if captain == vice:
        errors.append("Captain and vice-captain must be different players.")
    if captain not in start:
        errors.append("Captain must be a starter.")
    if vice not in start:
        errors.append("Vice-captain must be a starter.")

    return ValidationResult(
        accepted=not errors,
        errors=errors,
        data={
            "starters": start,
            "bench_outfield": bench,
            "reserve_gk": reserve,
            "captain_id": captain,
            "vice_captain_id": vice,
            "formation": {k: counts.get(k, 0) for k in ("GK", "DEF", "MID", "FWD")},
        },
    )


def formation_is_valid(positions: list[str], rules: Ruleset) -> bool:
    counts = Counter(positions)
    if counts.get("GK", 0) != 1:
        return False
    if not (rules.lineup["def"]["min"] <= counts.get("DEF", 0) <= rules.lineup["def"]["max"]):
        return False
    if not (rules.lineup["mid"]["min"] <= counts.get("MID", 0) <= rules.lineup["mid"]["max"]):
        return False
    if not (rules.lineup["fwd"]["min"] <= counts.get("FWD", 0) <= rules.lineup["fwd"]["max"]):
        return False
    return len(positions) == 11
