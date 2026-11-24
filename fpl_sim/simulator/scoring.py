from __future__ import annotations

from dataclasses import dataclass, field

from fpl_sim.simulator.autosubs import apply_auto_substitutions
from fpl_sim.simulator.captaincy import active_captain, captain_multiplier
from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.types import PlayerView


@dataclass
class PlayerScore:
    player_id: int
    raw_points: int
    multiplier: int
    counted_points: int
    started: bool
    bench_order: int | None
    auto_subbed_in: bool
    auto_subbed_out: bool


@dataclass
class GameweekScore:
    scores: list[PlayerScore]
    gross_points: int
    captain_id: int | None
    captain_contribution: int
    bench_points: int
    events: list = field(default_factory=list)


def score_gameweek(
    squad_ids: list[int],
    starters: list[int],
    bench_outfield: list[int],
    reserve_gk: int,
    captain_id: int,
    vice_captain_id: int,
    chip_type: str | None,
    minutes: dict[int, int],
    raw_points: dict[int, int],
    players: dict[int, PlayerView],
    rules: Ruleset,
) -> GameweekScore:
    new_starters, bench, reserve, events = apply_auto_substitutions(
        starters, bench_outfield, reserve_gk, minutes, players, rules
    )
    subbed_in = {e.player_in_id for e in events}
    subbed_out = {e.player_out_id for e in events}
    captain = active_captain(captain_id, vice_captain_id, minutes, rules)
    cap_mult = captain_multiplier(chip_type, rules)
    bench_boost = chip_type == "bboost"

    scores: list[PlayerScore] = []
    for pid in squad_ids:
        started = pid in new_starters
        raw = int(raw_points.get(pid, 0))
        if started:
            multiplier = cap_mult if captain is not None and pid == captain else 1
            bench_order = None
        else:
            multiplier = 1 if bench_boost else 0
            if pid == reserve:
                bench_order = None
            elif pid in bench:
                bench_order = bench.index(pid) + 1
            else:
                bench_order = None
        scores.append(
            PlayerScore(
                player_id=pid,
                raw_points=raw,
                multiplier=multiplier,
                counted_points=raw * multiplier,
                started=started,
                bench_order=bench_order,
                auto_subbed_in=pid in subbed_in,
                auto_subbed_out=pid in subbed_out,
            )
        )

    gross = sum(s.counted_points for s in scores)
    captain_contrib = 0
    if captain is not None:
        cap_score = next(s for s in scores if s.player_id == captain)
        captain_contrib = cap_score.counted_points
    bench_pts = sum(s.raw_points for s in scores if not s.started)
    return GameweekScore(
        scores=scores,
        gross_points=gross,
        captain_id=captain,
        captain_contribution=captain_contrib,
        bench_points=bench_pts,
        events=events,
    )
