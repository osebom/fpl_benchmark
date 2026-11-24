from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from fpl_sim.simulator.rules import FPLRulesEngine
from fpl_sim.tools.context import ToolContext
from fpl_sim.tools.schemas import CORE_V1
from fpl_sim.types import PendingDecision, SessionStats
from fpl_sim.world.context import WorldContext
from fpl_sim.world.historical_csv_world import HistoricalCSVWorld
from fpl_sim.world.repository import FPLWorldRepository

mcp = FastMCP("fpl-sim")
_ctx: ToolContext | None = None


def bind_context(ctx: ToolContext) -> None:
    global _ctx
    _ctx = ctx


def current_context() -> ToolContext:
    global _ctx
    if _ctx is None:
        gw = int(os.environ.get("FPL_CURRENT_GW", "1"))
        phase = os.environ.get("FPL_PHASE", "pre_deadline")
        repo = FPLWorldRepository(
            HistoricalCSVWorld(),
            WorldContext(current_gw=gw, phase=phase),  # type: ignore[arg-type]
        )
        _ctx = ToolContext(
            repo=repo,
            rules=FPLRulesEngine(),
            pending=PendingDecision(),
            stats=SessionStats(),
            manager_state={"bank_tenths": 1000, "free_transfers": 0, "player_ids": []},
            entitlements=[],
            gw1=gw == 1,
        )
    return _ctx


@mcp.tool()
def search_players(
    query: str | None = None,
    position: str | None = None,
    team_name: str | None = None,
    max_price: float | None = None,
    sort_by: str = "total_points",
    season: str = "current",
    min_minutes: float | None = None,
    limit: int = 15,
) -> dict[str, Any]:
    return current_context().search_players(
        query=query,
        position=position,
        team_name=team_name,
        max_price=max_price,
        sort_by=sort_by,
        season=season,
        min_minutes=min_minutes,
        limit=limit,
    )


@mcp.tool()
def get_player(player_id: int) -> dict[str, Any]:
    return current_context().get_player(player_id)


@mcp.tool()
def compare_players(player_ids: list[int]) -> dict[str, Any]:
    return current_context().compare_players(player_ids)


@mcp.tool()
def get_player_performance(player_id: int, last_n: int = 5) -> dict[str, Any]:
    return current_context().get_player_performance(player_id, last_n)


@mcp.tool()
def get_team_fixtures(team_id: int, next_n: int = 5) -> dict[str, Any]:
    return current_context().get_team_fixtures(team_id, next_n)


@mcp.tool()
def get_standings() -> dict[str, Any]:
    return current_context().get_standings()


@mcp.tool()
def get_historical_results(team_id: int | None = None, limit: int = 15) -> dict[str, Any]:
    return current_context().get_historical_results(team_id=team_id, limit=limit)


@mcp.tool()
def get_manager_state() -> dict[str, Any]:
    return current_context().get_manager_state()


@mcp.tool()
def submit_initial_squad(player_ids: list[int]) -> dict[str, Any]:
    return current_context().submit_initial_squad(player_ids)


@mcp.tool()
def submit_transfers(transfers: list[dict[str, Any]]) -> dict[str, Any]:
    return current_context().submit_transfers(transfers)


@mcp.tool()
def submit_lineup(
    starters: list[int],
    bench_outfield: list[int],
    reserve_gk: int,
    captain_id: int,
    vice_captain_id: int,
) -> dict[str, Any]:
    return current_context().submit_lineup(
        starters, bench_outfield, reserve_gk, captain_id, vice_captain_id
    )


@mcp.tool()
def play_chip(chip_type: str) -> dict[str, Any]:
    return current_context().play_chip(chip_type)


def main() -> None:
    _ = CORE_V1
    mcp.run()


if __name__ == "__main__":
    main()
