from fpl_sim.agents.scripted import ScriptedAgent
from fpl_sim.harness.gameweek_runner import Simulation
from fpl_sim.harness.reports import format_squad_pitch_html, gw_opponent_labels
from fpl_sim.storage.memory import InMemoryStore
from tests.conftest import legal_squad


def _lineup_call(built: dict) -> tuple[str, dict]:
    return (
        "submit_lineup",
        {
            "starters": built["starters"],
            "bench_outfield": built["bench_outfield"],
            "reserve_gk": built["reserve_gk"],
            "captain_id": built["captain_id"],
            "vice_captain_id": built["vice_captain_id"],
        },
    )


def test_select_and_resolve_gw1(repo_gw1, rules):
    built = legal_squad(repo_gw1, rules)
    gw1 = [
        ("submit_initial_squad", {"player_ids": built["player_ids"]}),
        _lineup_call(built),
    ]
    sim = Simulation.from_config(
        store=InMemoryStore(),
        agent=ScriptedAgent(gw1),
        start_mlflow=False,
    )
    decision = sim.select_initial_team()
    assert "GW1 DECISION" in decision
    gw_row = sim.store.get_gameweek(sim.simulation_id, 1)
    assert gw_row["status"] == "locked"
    assert len(sim.store.list_squad(gw_row["id"])) == 15
    result = sim.resolve_current()
    assert "GW1 RESULT" in result
    assert gw_row["status"] == "locked"
    done = sim.store.get_gameweek(sim.simulation_id, 1)
    assert done["status"] == "completed"
    assert done["net_points"] is not None


def test_advance_locks_gw2(repo_gw1, rules):
    built = legal_squad(repo_gw1, rules)
    same_lineup = [
        _lineup_call(built),
    ]
    gw1 = [
        ("submit_initial_squad", {"player_ids": built["player_ids"]}),
        _lineup_call(built),
    ]
    sim = Simulation.from_config(
        store=InMemoryStore(),
        agent=ScriptedAgent([gw1, same_lineup]),
        start_mlflow=False,
    )
    sim.select_initial_team()
    report = sim.advance()
    assert "GW1 RESULT" in report
    assert "GW2 DECISION" in report
    assert sim.store.get_gameweek(sim.simulation_id, 1)["status"] == "completed"
    assert sim.store.get_gameweek(sim.simulation_id, 2)["status"] == "locked"
    assert sim.store.get_simulation(sim.simulation_id)["current_gw"] == 2
    # unused FT from GW2 (0 transfers) stored after lock; started with 1
    gw2 = sim.store.get_gameweek(sim.simulation_id, 2)
    assert gw2["free_transfers"] == 1
    assert int(gw2["transfer_hit"] or 0) == 0


def test_pitch_html_includes_bank_and_selling_price(repo_gw1):
    player = next(iter(repo_gw1.current_player_map().values()))
    html = format_squad_pitch_html(
        [
            {
                "player_id": player.player_id,
                "selling_price": 6.0,
                "is_starter": True,
                "is_captain": True,
                "is_vice_captain": False,
                "bench_order": None,
            }
        ],
        {player.player_id: player},
        bank=4.5,
        team_value=100.5,
        gw=1,
        opponents_by_team={player.team_id: "vs Leeds (H)"},
        points_by_player={player.player_id: 8},
    )
    assert player.web_name in html
    assert player.team_name in html
    assert "Bank £4.5m" in html
    assert "TV £100.5m" in html
    assert "£6.0" in html
    assert "fpl-c" in html
    assert "vs Leeds (H)" in html
    assert "8 pts" in html
    html_net = format_squad_pitch_html(
        [
            {
                "player_id": player.player_id,
                "selling_price": 6.0,
                "is_starter": True,
                "is_captain": False,
                "is_vice_captain": False,
                "bench_order": None,
            }
        ],
        {player.player_id: player},
        bank=4.5,
        gw=1,
        points_by_player={player.player_id: 8},
        net_points=47,
        gross_points=47,
        transfer_hit=0,
    )
    assert "Net 47" in html_net
    assert "Gross 47" in html_net


def test_gw1_opponent_labels_cover_squad_clubs(repo_gw1):
    labels = gw_opponent_labels(repo_gw1, 1)
    assert labels
    sample = next(iter(repo_gw1.current_player_map().values()))
    assert sample.team_id in labels
    assert labels[sample.team_id].startswith("vs ")


def test_pitch_html_chip_on_bb_tc_and_autosub(repo_gw1):
    player = next(iter(repo_gw1.current_player_map().values()))
    pid = player.player_id
    chips = [
        {
            "chip_type": "wildcard",
            "available_from_gw": 2,
            "expires_after_gw": 19,
            "used_gw": None,
        },
        {
            "chip_type": "bboost",
            "available_from_gw": 1,
            "expires_after_gw": 19,
            "used_gw": 2,
        },
        {
            "chip_type": "3xc",
            "available_from_gw": 1,
            "expires_after_gw": 19,
            "used_gw": None,
        },
    ]
    html = format_squad_pitch_html(
        [
            {
                "player_id": pid,
                "selling_price": 6.0,
                "is_starter": True,
                "is_captain": True,
                "is_vice_captain": False,
                "bench_order": None,
            }
        ],
        {pid: player},
        bank=4.5,
        gw=2,
        chips=chips,
        active_chip="bboost",
        bench_boost=True,
        points_by_player={pid: 8},
        multipliers_by_player={pid: 1},
        autosub_notes={pid: "▲ in for Bench"},
    )
    assert "fpl-chip-on" in html
    assert "BB 1–19 · ON" in html
    assert "fpl-chip-ready" in html
    assert "WC 2–19" in html
    assert "fpl-bb" in html
    assert "BENCH BOOST" in html
    assert "▲ in for Bench" in html
    html_tc = format_squad_pitch_html(
        [
            {
                "player_id": pid,
                "selling_price": 6.0,
                "is_starter": True,
                "is_captain": True,
                "is_vice_captain": False,
                "bench_order": None,
            }
        ],
        {pid: player},
        bank=4.5,
        gw=2,
        chips=[
            {
                "chip_type": "3xc",
                "available_from_gw": 1,
                "expires_after_gw": 19,
                "used_gw": 2,
            }
        ],
        active_chip="3xc",
        points_by_player={pid: 24},
        multipliers_by_player={pid: 3},
    )
    assert "fpl-tc" in html_tc
    assert "24 pts" in html_tc
    assert "×3" not in html_tc
    assert "×2" not in html_tc
    assert "TC 1–19 · ON" in html_tc
