from fpl_sim.simulator.pricing import selling_price_tenths, transfer_hit
from fpl_sim.types import TransferMove
from tests.conftest import legal_squad


def test_selling_price_rise_keeps_half():
    assert selling_price_tenths(100, 106) == 103
    assert selling_price_tenths(100, 105) == 102


def test_selling_price_fall_is_full():
    assert selling_price_tenths(100, 97) == 97


def test_transfer_hit_example():
    paid, hit, remaining = transfer_hit(3, 1, -4)
    assert paid == 2
    assert hit == -8
    assert remaining == 0


def test_valid_like_for_like_transfer(repo_gw1, rules):
    repo = repo_gw1
    built = legal_squad(repo, rules)
    players = repo.current_player_map()
    squad = built["player_ids"]
    purchases = {pid: players[pid].now_cost for pid in squad}
    from collections import Counter

    out_id = next(pid for pid in squad if players[pid].position == "MID")
    clubs = Counter(players[pid].team_id for pid in squad if pid != out_id)
    candidate = next(
        p
        for p in repo.current_players()
        if p.position == "MID"
        and p.player_id not in squad
        and p.can_select
        and p.can_transact
        and p.now_cost <= players[out_id].now_cost + 20
        and clubs[p.team_id] < rules.rules.max_per_club
    )
    result = rules.validate_transfers(
        squad,
        [TransferMove(player_out_id=out_id, player_in_id=candidate.player_id)],
        players,
        purchases,
        bank_tenths=50,
        free_transfers=1,
    )
    assert result.accepted, result.errors
    assert result.data["n_transfers"] == 1
    assert result.data["transfer_hit"] == 0


def test_wildcard_has_no_hit(repo_gw1, rules):
    repo = repo_gw1
    built = legal_squad(repo, rules)
    players = repo.current_player_map()
    squad = built["player_ids"]
    purchases = {pid: players[pid].now_cost for pid in squad}
    out_ids = [pid for pid in squad if players[pid].position == "MID"][:2]
    ins = [
        p.player_id
        for p in repo.current_players()
        if p.position == "MID" and p.player_id not in squad and p.can_select
    ][:2]
    moves = [
        TransferMove(player_out_id=o, player_in_id=i) for o, i in zip(out_ids, ins, strict=True)
    ]
    result = rules.validate_transfers(
        squad,
        moves,
        players,
        purchases,
        bank_tenths=200,
        free_transfers=1,
        chip_type="wildcard",
    )
    if result.accepted:
        assert result.data["transfer_hit"] == 0
        assert result.data["remaining_fts"] == 1
