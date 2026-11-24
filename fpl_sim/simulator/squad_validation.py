from __future__ import annotations

from collections import Counter

from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.types import PlayerView, ValidationResult


def validate_initial_squad(
    player_ids: list[int],
    players: dict[int, PlayerView],
    rules: Ruleset,
    budget_tenths: int | None = None,
) -> ValidationResult:
    errors: list[str] = []
    ids = [int(x) for x in player_ids]
    if len(ids) != 15:
        errors.append(f"Squad must contain exactly 15 players, got {len(ids)}.")
    if len(set(ids)) != len(ids):
        errors.append("Squad contains duplicate players.")

    missing = [pid for pid in ids if pid not in players]
    if missing:
        errors.append(f"Unknown or unavailable player ids: {missing}.")
        return ValidationResult.fail(*errors)

    selected = [players[pid] for pid in ids]
    unselectable = [p.web_name for p in selected if not p.can_select or p.removed]
    if unselectable:
        errors.append(f"Players are not selectable at this deadline: {unselectable}.")

    counts = Counter(p.position for p in selected)
    for pos, needed in rules.squad_positions.items():
        actual = counts.get(pos, 0)
        if actual != needed:
            errors.append(f"Squad needs {needed} {pos}, got {actual}.")

    club_counts = Counter(p.team_id for p in selected)
    over = {players[next(pid for pid in ids if players[pid].team_id == tid)].team_name: n
            for tid, n in club_counts.items() if n > rules.max_per_club}
    if over:
        details = ", ".join(f"{name}={n}" for name, n in over.items())
        errors.append(f"Maximum {rules.max_per_club} players per club. Over limit: {details}.")

    cost = sum(p.now_cost for p in selected)
    budget = rules.initial_budget_tenths if budget_tenths is None else int(budget_tenths)
    if cost > budget:
        errors.append(
            f"Squad costs £{cost / 10:.1f}m which exceeds the £{budget / 10:.1f}m budget."
        )

    bank = budget - cost
    return ValidationResult(
        accepted=not errors,
        errors=errors,
        data={"bank_tenths": bank, "cost_tenths": cost, "player_ids": ids},
    )
