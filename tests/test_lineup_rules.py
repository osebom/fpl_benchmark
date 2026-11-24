from tests.conftest import legal_squad


def test_valid_lineup(repo_gw1, rules):
    built = legal_squad(repo_gw1, rules)
    result = rules.validate_lineup(
        built["player_ids"],
        built["starters"],
        built["bench_outfield"],
        built["reserve_gk"],
        built["captain_id"],
        built["vice_captain_id"],
        repo_gw1.current_player_map(),
    )
    assert result.accepted, result.errors
    assert result.data["formation"]["GK"] == 1
    assert result.data["formation"]["DEF"] == 3


def test_two_defenders_illegal(repo_gw1, rules):
    built = legal_squad(repo_gw1, rules)
    players = repo_gw1.current_player_map()
    starters = list(built["starters"])
    defs = [pid for pid in starters if players[pid].position == "DEF"]
    mids_bench = [pid for pid in built["bench_outfield"] if players[pid].position == "MID"]
    if not mids_bench:
        return
    starters.remove(defs[0])
    starters.append(mids_bench[0])
    bench = [defs[0] if pid == mids_bench[0] else pid for pid in built["bench_outfield"]]
    result = rules.validate_lineup(
        built["player_ids"],
        starters,
        bench,
        built["reserve_gk"],
        starters[-1],
        starters[-2],
        players,
    )
    # 2 DEF is illegal
    if sum(1 for pid in starters if players[pid].position == "DEF") < 3:
        assert not result.accepted


def test_captain_must_start(repo_gw1, rules):
    built = legal_squad(repo_gw1, rules)
    result = rules.validate_lineup(
        built["player_ids"],
        built["starters"],
        built["bench_outfield"],
        built["reserve_gk"],
        built["bench_outfield"][0],
        built["vice_captain_id"],
        repo_gw1.current_player_map(),
    )
    assert not result.accepted
    assert any("Captain" in e for e in result.errors)
