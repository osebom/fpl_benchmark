from fpl_sim.world.context import WorldContext
from fpl_sim.world.repository import FPLWorldRepository


def test_pre_gw1_has_no_performances(world):
    repo = FPLWorldRepository(world, WorldContext(current_gw=1, phase="pre_deadline"))
    assert repo.latest_completed_gw is None
    assert repo.player_performance(1, last_n=5) == []
    assert repo.awards() == []
    assert repo.current_standings() == []
    assert repo.gw_performance_map


def test_pre_gw1_cannot_read_gw1_points(world):
    repo = FPLWorldRepository(world, WorldContext(current_gw=1, phase="pre_deadline"))
    try:
        repo.gw_performance_map(1)
        raise AssertionError("GW1 performance should be hidden before the deadline")
    except PermissionError:
        pass


def test_post_gw1_can_read_gw1_points(world):
    repo = FPLWorldRepository(world, WorldContext(current_gw=1, phase="post_gameweek"))
    perf = repo.gw_performance_map(1)
    assert perf
    assert 1 in perf or next(iter(perf))


def test_pre_gw12_window(world):
    repo = FPLWorldRepository(world, WorldContext(current_gw=12, phase="pre_deadline"))
    rows = repo.player_performance(1, last_n=20)
    gws = {r["gameweek"] for r in rows}
    assert 11 in gws
    assert 12 not in gws
    assert 13 not in gws
    awards = repo.awards()
    assert max(a["gameweek"] for a in awards) == 11
    assert repo.awards_for_gw(12) is None
    try:
        repo.gw_performance_map(12)
        raise AssertionError("expected leakage protection")
    except PermissionError:
        pass


def test_pre_gw12_uses_pre_gw12_snapshot_not_later(world):
    repo12 = FPLWorldRepository(world, WorldContext(current_gw=12, phase="pre_deadline"))
    repo13 = FPLWorldRepository(world, WorldContext(current_gw=13, phase="pre_deadline"))
    p12 = {p.player_id: p.now_cost for p in repo12.current_players()}
    p13 = {p.player_id: p.now_cost for p in repo13.current_players()}
    assert repo12.context.current_gw == 12
    # snapshots are distinct files; at least one price or membership should differ
    assert p12 != p13 or set(p12) != set(p13)


def test_pre_deadline_fixtures_are_current_snapshot(world):
    repo = FPLWorldRepository(world, WorldContext(current_gw=5, phase="pre_deadline"))
    fixtures = repo.current_fixtures()
    assert fixtures
    assert all(int(f["snapshot_gameweek"]) == 5 for f in fixtures)


def test_every_gw_pre_deadline_hides_current_performance(world):
    for gw in (2, 10, 19, 20, 38):
        repo = FPLWorldRepository(world, WorldContext(current_gw=gw, phase="pre_deadline"))
        latest = repo.latest_completed_gw
        assert latest == gw - 1
        try:
            repo.gw_performance_map(gw)
            raise AssertionError(f"GW{gw} points leaked")
        except PermissionError:
            pass
        if gw < 38:
            try:
                repo.gw_performance_map(gw + 1)
                raise AssertionError(f"GW{gw+1} points leaked")
            except PermissionError:
                pass
        if latest:
            assert repo.gw_performance_map(latest)
