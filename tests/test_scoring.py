from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.simulator.scoring import score_gameweek
from fpl_sim.types import PlayerView


def _player(pid: int, position: str) -> PlayerView:
    return PlayerView(
        player_id=pid,
        web_name=str(pid),
        team_id=1,
        team_name="X",
        position=position,  # type: ignore[arg-type]
        element_type={"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}[position],
        now_cost=50,
        price=5.0,
    )


def _squad():
    players = {}
    positions = (
        ["GK"]
        + ["DEF"] * 3
        + ["MID"] * 4
        + ["FWD"] * 3
        + ["GK"]
        + ["DEF"]
        + ["MID"]
        + ["FWD"]
    )
    for i, pos in enumerate(positions, start=1):
        players[i] = _player(i, pos)
    starters = list(range(1, 12))
    bench = [13, 14, 15]
    return players, starters, bench, 12


def test_captain_doubles_when_they_appear():
    rules = Ruleset.load()
    players, starters, bench, reserve = _squad()
    minutes = {i: 90 for i in range(1, 16)}
    raw = {i: 6 for i in range(1, 16)}
    raw[11] = 10
    scored = score_gameweek(
        list(range(1, 16)), starters, bench, reserve, 11, 10, None, minutes, raw, players, rules
    )
    cap = next(s for s in scored.scores if s.player_id == 11)
    assert cap.multiplier == 2
    assert cap.counted_points == 20
    assert scored.captain_contribution == 20


def test_vice_captain_fallback():
    rules = Ruleset.load()
    players, starters, bench, reserve = _squad()
    minutes = {i: 90 for i in range(1, 16)}
    minutes[11] = 0
    raw = {i: 4 for i in range(1, 16)}
    raw[10] = 8
    scored = score_gameweek(
        list(range(1, 16)), starters, bench, reserve, 11, 10, None, minutes, raw, players, rules
    )
    assert scored.captain_id == 10
    cap = next(s for s in scored.scores if s.player_id == 10)
    assert cap.multiplier == 2
    assert cap.counted_points == 16


def test_neither_captain_appears():
    rules = Ruleset.load()
    players, starters, bench, reserve = _squad()
    minutes = {i: 90 for i in range(1, 16)}
    minutes[11] = 0
    minutes[10] = 0
    raw = {i: 4 for i in range(1, 16)}
    scored = score_gameweek(
        list(range(1, 16)), starters, bench, reserve, 11, 10, None, minutes, raw, players, rules
    )
    assert scored.captain_id is None
    assert all(s.multiplier in (0, 1) for s in scored.scores)


def test_triple_captain():
    rules = Ruleset.load()
    players, starters, bench, reserve = _squad()
    minutes = {i: 90 for i in range(1, 16)}
    raw = {i: 3 for i in range(1, 16)}
    raw[11] = 9
    scored = score_gameweek(
        list(range(1, 16)), starters, bench, reserve, 11, 10, "3xc", minutes, raw, players, rules
    )
    cap = next(s for s in scored.scores if s.player_id == 11)
    assert cap.multiplier == 3
    assert cap.counted_points == 27


def test_bench_boost_counts_bench():
    rules = Ruleset.load()
    players, starters, bench, reserve = _squad()
    minutes = {i: 90 for i in range(1, 16)}
    raw = {i: 2 for i in range(1, 16)}
    scored = score_gameweek(
        list(range(1, 16)), starters, bench, reserve, 11, 10, "bboost", minutes, raw, players, rules
    )
    bench_scores = [s for s in scored.scores if not s.started]
    assert all(s.multiplier == 1 for s in bench_scores)
    assert scored.gross_points == 2 * 15 + 2  # 15 players * 2, captain extra +2
