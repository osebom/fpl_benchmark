from __future__ import annotations

from collections import Counter

import pytest

from fpl_sim.simulator.rules import FPLRulesEngine
from fpl_sim.world.context import WorldContext
from fpl_sim.world.historical_csv_world import HistoricalCSVWorld
from fpl_sim.world.repository import FPLWorldRepository


@pytest.fixture(scope="session")
def world() -> HistoricalCSVWorld:
    return HistoricalCSVWorld()


@pytest.fixture
def rules() -> FPLRulesEngine:
    return FPLRulesEngine()


@pytest.fixture
def repo_gw1(world) -> FPLWorldRepository:
    return FPLWorldRepository(world, WorldContext(current_gw=1, phase="pre_deadline"))


def legal_squad(repo: FPLWorldRepository, rules: FPLRulesEngine) -> dict:
    """Cheapest legal 15 + a valid XI from the current snapshot."""
    players = [p for p in repo.current_players() if p.can_select and not p.removed]
    players.sort(key=lambda p: (p.now_cost, p.player_id))
    needed = dict(rules.rules.squad_positions)
    chosen = []
    clubs: Counter[int] = Counter()
    for player in players:
        if needed.get(player.position, 0) <= 0:
            continue
        if clubs[player.team_id] >= rules.rules.max_per_club:
            continue
        chosen.append(player)
        needed[player.position] -= 1
        clubs[player.team_id] += 1
        if sum(needed.values()) == 0:
            break
    if sum(needed.values()) != 0:
        raise RuntimeError(f"Could not build a legal squad, remaining {needed}")
    ids = [p.player_id for p in chosen]
    by_pos = {"GK": [], "DEF": [], "MID": [], "FWD": []}
    for player in chosen:
        by_pos[player.position].append(player.player_id)
    starters = [by_pos["GK"][0]] + by_pos["DEF"][:3] + by_pos["MID"][:4] + by_pos["FWD"][:3]
    bench_outfield = [pid for pid in ids if pid not in starters and pid != by_pos["GK"][1]]
    # 3 DEF + 4 MID + 3 FWD + 1 GK = 11. Remaining outfield = 2 DEF + 1 MID = 3.
    reserve = by_pos["GK"][1]
    return {
        "player_ids": ids,
        "starters": starters,
        "bench_outfield": bench_outfield,
        "reserve_gk": reserve,
        "captain_id": starters[-1],
        "vice_captain_id": starters[-2],
        "players": {p.player_id: p for p in chosen},
    }
