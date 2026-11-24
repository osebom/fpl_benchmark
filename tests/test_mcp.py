from fpl_sim.mcp.server import current_context, search_players


def test_mcp_wrappers_use_shared_tools():
    ctx = current_context()
    assert ctx.repo.current_gw == 1
    result = search_players(position="FWD", limit=3)
    assert "players" in result
    assert len(result["players"]) <= 3
