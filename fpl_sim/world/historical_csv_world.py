from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from fpl_sim.paths import data_dir


def gw_tag(gw: int) -> str:
    return f"{gw:02d}"


class HistoricalCSVWorld:
    """Read-only loader for the versioned final_fpl CSV dataset."""

    def __init__(self, root: Path | None = None, dataset_version: str = "v1") -> None:
        self.root = Path(root) if root is not None else data_dir()
        self.dataset_version = dataset_version
        if not self.root.exists():
            raise FileNotFoundError(f"final_fpl dataset not found at {self.root}")

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def player_snapshot(self, gw: int) -> pd.DataFrame:
        if gw == 1:
            return _read_csv(self.path("pre_gw01_player_profiles.csv"))
        return _read_csv(self.path("gw_player_profile", f"pre_gw{gw_tag(gw)}_player_stats.csv"))

    def fixtures_snapshot(self, gw: int) -> pd.DataFrame:
        return _read_csv(self.path("gw_fixtures_snapshots", f"pre_gw{gw_tag(gw)}.csv"))

    def standings_snapshot(self, gw: int) -> pd.DataFrame:
        if gw < 2:
            return pd.DataFrame()
        return _read_csv(self.path("gw_standings", f"pre_gw{gw_tag(gw)}_standings.csv"))

    def player_performance(self, gw: int) -> pd.DataFrame:
        return _read_csv(
            self.path("gw_player_performances", f"gw{gw_tag(gw)}_player_performance.csv")
        )

    def player_fixture_stats(self, gw: int) -> pd.DataFrame:
        return _read_csv(
            self.path("gw_player_fixture_stats", f"gw{gw_tag(gw)}_player_fixture_stats.csv")
        )

    def results_through(self, gw: int) -> pd.DataFrame:
        return _read_csv(self.path("gw_results_details", f"results_through_gw{gw_tag(gw)}.csv"))

    def awards(self) -> pd.DataFrame:
        return _read_csv(self.path("gw_awards", "gameweek_awards.csv"))

    def chip_usage(self) -> pd.DataFrame:
        return _read_csv(self.path("gw_awards", "chip_usage.csv"))

    def totw(self, gw: int | None = None) -> pd.DataFrame:
        all_rows = _read_csv(self.path("gw_awards", "gameweek_totw.csv"))
        if gw is None:
            return all_rows
        return all_rows[all_rows["gameweek"] == gw].copy()

    def historical_results(self) -> pd.DataFrame:
        return _read_csv(self.path("historical_match_results", "past_3_seasons_results.csv"))


@lru_cache(maxsize=256)
def _read_csv(path: Path) -> pd.DataFrame:
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    return pd.read_csv(resolved)
