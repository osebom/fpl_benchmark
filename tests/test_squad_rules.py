from tests.conftest import legal_squad


def test_legal_cheap_squad(repo_gw1, rules):
    built = legal_squad(repo_gw1, rules)
    result = rules.validate_initial_squad(built["player_ids"], repo_gw1.current_player_map())
    assert result.accepted, result.errors
    assert result.data["bank_tenths"] >= 0


def test_squad_wrong_counts(repo_gw1, rules):
    built = legal_squad(repo_gw1, rules)
    ids = built["player_ids"][:-1]
    result = rules.validate_initial_squad(ids, repo_gw1.current_player_map())
    assert not result.accepted


def test_squad_over_budget(repo_gw1, rules):
    players = repo_gw1.current_player_map()
    expensive = sorted(players.values(), key=lambda p: -p.now_cost)
    # grab 15 unique regardless of legality except count
    ids = [p.player_id for p in expensive[:15]]
    result = rules.validate_initial_squad(ids, players, budget_tenths=100)
    assert not result.accepted


def test_club_limit(repo_gw1, rules):
    players = [p for p in repo_gw1.current_players() if p.can_select]
    arsenal = [p for p in players if p.team_name == "Arsenal"]
    if len(arsenal) < 4:
        return
    built = legal_squad(repo_gw1, rules)
    # force 4 arsenal if possible by replacing
    ids = built["player_ids"]
    extras = [p.player_id for p in arsenal if p.player_id not in ids][:4]
    if len(extras) < 1:
        return
    bloated = ids[:11] + extras[:4]
    result = rules.validate_initial_squad(bloated, repo_gw1.current_player_map())
    assert not result.accepted
    assert any("club" in e.lower() or "Arsenal" in e for e in result.errors)
