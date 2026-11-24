from __future__ import annotations

from dataclasses import dataclass

from fpl_sim.simulator.lineup_validation import formation_is_valid
from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.types import PlayerView


@dataclass
class AutoSubEvent:
    player_in_id: int
    player_out_id: int
    kind: str  # gk | outfield


def apply_auto_substitutions(
    starters: list[int],
    bench_outfield: list[int],
    reserve_gk: int,
    minutes: dict[int, int],
    players: dict[int, PlayerView],
    rules: Ruleset,
) -> tuple[list[int], list[int], int, list[AutoSubEvent]]:
    """Return (new_starters, new_bench, new_reserve_gk, events) after official auto-subs."""
    start = list(starters)
    bench = list(bench_outfield)
    reserve = int(reserve_gk)
    events: list[AutoSubEvent] = []
    used_bench: set[int] = set()

    starting_gk = next(pid for pid in start if players[pid].position == "GK")
    if minutes.get(starting_gk, 0) < 1 and minutes.get(reserve, 0) >= 1:
        start = [reserve if pid == starting_gk else pid for pid in start]
        events.append(AutoSubEvent(player_in_id=reserve, player_out_id=starting_gk, kind="gk"))
        reserve = starting_gk

    missing = [pid for pid in start if players[pid].position != "GK" and minutes.get(pid, 0) < 1]
    for missing_id in missing:
        for bench_id in bench:
            if bench_id in used_bench:
                continue
            if minutes.get(bench_id, 0) < 1:
                continue
            trial = [bench_id if pid == missing_id else pid for pid in start]
            trial_positions = [players[pid].position for pid in trial]
            if not formation_is_valid(trial_positions, rules):
                continue
            start = trial
            used_bench.add(bench_id)
            events.append(AutoSubEvent(player_in_id=bench_id, player_out_id=missing_id, kind="outfield"))
            break

    return start, bench, reserve, events
