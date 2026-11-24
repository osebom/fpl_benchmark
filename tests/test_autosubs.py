from fpl_sim.simulator.autosubs import apply_auto_substitutions
from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.types import PlayerView


def _player(pid: int, position: str) -> PlayerView:
    return PlayerView(
        player_id=pid,
        web_name=str(pid),
        team_id=pid,
        team_name="X",
        position=position,  # type: ignore[arg-type]
        element_type={"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}[position],
        now_cost=50,
        price=5.0,
    )


def test_formation_blocked_bench_skip():
    """Starting 3 DEF / 4 MID / 3 FWD. A DEF blanks. Bench is FWD, MID, DEF.
    FWD and MID cannot come on; the DEF should.
    """
    rules = Ruleset.load()
    players = {
        1: _player(1, "GK"),
        2: _player(2, "DEF"),
        3: _player(3, "DEF"),
        4: _player(4, "DEF"),
        5: _player(5, "MID"),
        6: _player(6, "MID"),
        7: _player(7, "MID"),
        8: _player(8, "MID"),
        9: _player(9, "FWD"),
        10: _player(10, "FWD"),
        11: _player(11, "FWD"),
        12: _player(12, "GK"),
        13: _player(13, "FWD"),
        14: _player(14, "MID"),
        15: _player(15, "DEF"),
    }
    starters = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    bench = [13, 14, 15]
    minutes = {pid: 90 for pid in starters + bench + [12]}
    minutes[2] = 0  # starting DEF blanks
    minutes[13] = 90
    minutes[14] = 90
    minutes[15] = 90
    new_start, _, _, events = apply_auto_substitutions(starters, bench, 12, minutes, players, rules)
    assert events
    assert events[0].player_out_id == 2
    assert events[0].player_in_id == 15
    assert 15 in new_start
    assert 2 not in new_start


def test_gk_sub_is_separate():
    rules = Ruleset.load()
    players = {1: _player(1, "GK"), 12: _player(12, "GK")}
    for pid, pos in [
        (2, "DEF"),
        (3, "DEF"),
        (4, "DEF"),
        (5, "MID"),
        (6, "MID"),
        (7, "MID"),
        (8, "MID"),
        (9, "FWD"),
        (10, "FWD"),
        (11, "FWD"),
        (13, "DEF"),
        (14, "MID"),
        (15, "FWD"),
    ]:
        players[pid] = _player(pid, pos)
    starters = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    minutes = {pid: 90 for pid in range(1, 16)}
    minutes[1] = 0
    new_start, _, reserve, events = apply_auto_substitutions(
        starters, [13, 14, 15], 12, minutes, players, rules
    )
    assert any(e.kind == "gk" for e in events)
    assert 12 in new_start
    assert reserve == 1
