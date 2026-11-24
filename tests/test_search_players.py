from fpl_sim.tools.context import ToolContext
from fpl_sim.types import PendingDecision, SessionStats
from fpl_sim.world.context import WorldContext
from fpl_sim.world.repository import FPLWorldRepository


def test_gw1_search_ranks_last_season_points(repo_gw1):
    ranked = repo_gw1.search_players(
        position="FWD",
        sort_by="total_points",
        season="2024_25",
        limit=5,
    )
    assert ranked
    values = [
        repo_gw1._metric(p, "total_points", "2024_25")[0] for p in ranked
    ]
    assert values == sorted(values, reverse=True)
    assert ranked[0].history_2024_25
    assert (ranked[0].history_2024_25 or {}).get("total_points")


def test_gw1_defensive_contribution_is_on_last_season_history(repo_gw1):
    ranked = repo_gw1.search_players(
        position="MID",
        sort_by="defensive_contribution",
        season="2024_25",
        min_minutes=900,
        limit=8,
    )
    assert ranked
    dcs = [
        repo_gw1._metric(p, "defensive_contribution", "2024_25")[0] for p in ranked
    ]
    assert dcs == sorted(dcs, reverse=True)
    assert dcs[0] > 0
    hist = ranked[0].history_2024_25 or {}
    assert hist.get("defensive_contribution") == ranked[0].defensive_contribution


def test_forwards_are_not_the_dc_leaders(repo_gw1):
    mids = repo_gw1.search_players(
        position="MID", sort_by="defensive_contribution", season="2024_25", limit=1
    )
    fwds = repo_gw1.search_players(
        position="FWD", sort_by="defensive_contribution", season="2024_25", limit=1
    )
    mid_dc = repo_gw1._metric(mids[0], "defensive_contribution", "2024_25")[0]
    fwd_dc = repo_gw1._metric(fwds[0], "defensive_contribution", "2024_25")[0]
    assert mid_dc > fwd_dc


def test_prior_season_history_survives_after_gw1(world):
    repo = FPLWorldRepository(world, WorldContext(current_gw=5, phase="pre_deadline"))
    ranked = repo.search_players(
        position="DEF",
        sort_by="clean_sheets",
        season="2024_25",
        limit=3,
    )
    assert ranked
    assert ranked[0].history_2024_25
    current_cs = ranked[0].clean_sheets or 0
    prior_cs = (ranked[0].history_2024_25 or {}).get("clean_sheets") or 0
    assert prior_cs >= current_cs


def test_tool_search_returns_sort_value_and_history(repo_gw1, rules):
    ctx = ToolContext(
        repo=repo_gw1,
        rules=rules,
        pending=PendingDecision(),
        stats=SessionStats(),
        manager_state={"bank_tenths": 1000, "player_ids": []},
        entitlements=[],
        gw1=True,
    )
    result = ctx.search_players(
        position="GK",
        sort_by="saves",
        season="2024_25",
        limit=3,
    )
    assert result["count"] == 3
    assert result["sort_by"] == "saves"
    assert result["players"][0]["sort_value"] >= result["players"][1]["sort_value"]
    assert "history_2024_25" in result["players"][0]
    assert result["players"][0]["history_2024_25"]["saves"] == result["players"][0]["sort_value"]


def test_unknown_sort_is_rejected(repo_gw1, rules):
    ctx = ToolContext(
        repo=repo_gw1,
        rules=rules,
        pending=PendingDecision(),
        stats=SessionStats(),
        manager_state={"bank_tenths": 1000, "player_ids": []},
        entitlements=[],
        gw1=True,
    )
    result = ctx.search_players(sort_by="magic")
    assert result["accepted"] is False
