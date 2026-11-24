from fpl_sim.simulator.pricing import selling_price_tenths
from fpl_sim.tools.context import ToolContext
from fpl_sim.types import PendingDecision, SessionStats, tenths_to_millions
from tests.conftest import legal_squad


def _ctx(repo_gw1, rules, *, gw1=True, entitlements=None, manager_state=None):
    return ToolContext(
        repo=repo_gw1,
        rules=rules,
        pending=PendingDecision(),
        stats=SessionStats(),
        manager_state=manager_state
        or {"bank_tenths": 1000, "free_transfers": 0, "player_ids": [], "purchase_prices": {}},
        entitlements=entitlements or list(rules.rules.chip_entitlements),
        gw1=gw1,
    )


def test_lineup_locks_without_finalize(repo_gw1, rules):
    built = legal_squad(repo_gw1, rules)
    ctx = _ctx(repo_gw1, rules)
    squad = ctx.submit_initial_squad(built["player_ids"])
    assert squad["accepted"]
    assert not ctx.finalized
    lineup = ctx.submit_lineup(
        built["starters"],
        built["bench_outfield"],
        built["reserve_gk"],
        built["captain_id"],
        built["vice_captain_id"],
    )
    assert lineup["accepted"]
    assert ctx.finalized
    again = ctx.submit_lineup(
        built["starters"],
        built["bench_outfield"],
        built["reserve_gk"],
        built["captain_id"],
        built["vice_captain_id"],
    )
    assert not again["accepted"]


def test_gw1_tells_you_to_submit_squad_first(repo_gw1, rules):
    ctx = _ctx(repo_gw1, rules)
    result = ctx.submit_lineup([1] * 11, [2, 3, 4], 5, 1, 2)
    assert not result["accepted"]
    assert "submit_initial_squad" in result["errors"][0]
    transfers = ctx.submit_transfers([{"player_out_id": 1, "player_in_id": 2}])
    assert not transfers["accepted"]
    assert "submit_initial_squad" in transfers["errors"][0]


def test_manager_state_selling_price_and_chip_filter(repo_gw1, rules):
    built = legal_squad(repo_gw1, rules)
    pid = built["player_ids"][0]
    player = repo_gw1.current_player_map()[pid]
    entitlements = []
    for i, row in enumerate(rules.rules.chip_entitlements):
        item = dict(row)
        item["id"] = str(i)
        if item["chip_type"] == "3xc" and item["available_from_gw"] == 1:
            item["used_gw"] = 1
        entitlements.append(item)
    ctx = _ctx(
        repo_gw1,
        rules,
        entitlements=entitlements,
        manager_state={
            "bank_tenths": 1000,
            "free_transfers": 0,
            "player_ids": [],
            "purchase_prices": {pid: player.now_cost - 2},
        },
    )
    ctx.submit_initial_squad(built["player_ids"])
    state = ctx.get_manager_state()
    owned = next(row for row in state["squad"] if row["player_id"] == pid)
    assert "purchase_price" not in owned
    assert owned["selling_price"] == tenths_to_millions(
        selling_price_tenths(player.now_cost, player.now_cost)
    )
    chip_types = {c["chip_type"] for c in state["chips"]}
    assert "wildcard" not in chip_types
    assert "3xc" in chip_types
    assert all(c["available_from_gw"] <= 1 <= c["expires_after_gw"] for c in state["chips"])
