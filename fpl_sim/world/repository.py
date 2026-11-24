from __future__ import annotations

from typing import Any

import pandas as pd

from fpl_sim.types import ELEMENT_TYPE_TO_POSITION, PlayerView, tenths_to_millions
from fpl_sim.world.context import WorldContext
from fpl_sim.world.historical_csv_world import HistoricalCSVWorld

RESULT_AWARD_FIELDS = (
    "average_manager_score",
    "highest_manager_score",
    "player_of_gameweek_id",
    "player_of_gameweek_name",
    "player_of_gameweek_team_id",
    "player_of_gameweek_team_name",
    "player_of_gameweek_points",
)

COMPACT_PLAYER_FIELDS = (
    "player_id",
    "web_name",
    "team_id",
    "team_name",
    "position",
    "price",
    "status",
    "news",
    "chance_of_playing_this_round",
    "form",
    "total_points",
    "minutes",
    "starts",
    "goals_scored",
    "assists",
    "clean_sheets",
    "defensive_contribution",
    "tackles",
    "clearances_blocks_interceptions",
    "expected_goals",
    "expected_assists",
    "saves",
    "selected_by_percent",
    "ep_this",
    "ep_next",
)

HISTORY_COMPACT_FIELDS = (
    "total_points",
    "minutes",
    "starts",
    "goals_scored",
    "assists",
    "clean_sheets",
    "defensive_contribution",
    "tackles",
    "clearances_blocks_interceptions",
    "expected_goals",
    "expected_assists",
    "saves",
    "bonus",
)

SEARCH_SORT_FIELDS = (
    "total_points",
    "minutes",
    "starts",
    "goals_scored",
    "assists",
    "clean_sheets",
    "defensive_contribution",
    "tackles",
    "clearances_blocks_interceptions",
    "expected_goals",
    "expected_assists",
    "saves",
    "bonus",
    "form",
    "selected_by_percent",
    "ict_index",
    "price",
    "now_cost",
)

SEARCH_SEASONS = ("current", "2024_25", "2023_24", "prior")
ASCENDING_SORT = {"price", "now_cost"}
PRIOR_DEFENSIVE_FIELDS = (
    "defensive_contribution",
    "tackles",
    "clearances_blocks_interceptions",
)


def _clean(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


def _row_get(row: pd.Series, *names: str, default: Any = None) -> Any:
    for name in names:
        if name in row.index:
            return _clean(row[name])
    return default


def _bool(value: Any, default: bool = True) -> bool:
    cleaned = _clean(value)
    if cleaned is None:
        return default
    if isinstance(cleaned, str):
        return cleaned.lower() in {"true", "1", "yes"}
    return bool(cleaned)


def _history_block(row: pd.Series, prefix: str) -> dict[str, Any] | None:
    available = _bool(_row_get(row, f"{prefix}_available"), default=False)
    if not available and f"{prefix}_total_points" not in row.index:
        return None
    total_points = _row_get(row, f"{prefix}_total_points")
    if total_points is None and not available:
        return None
    return {
        "available": available,
        "total_points": total_points,
        "minutes": _row_get(row, f"{prefix}_minutes"),
        "starts": _row_get(row, f"{prefix}_starts"),
        "goals_scored": _row_get(row, f"{prefix}_goals_scored"),
        "assists": _row_get(row, f"{prefix}_assists"),
        "clean_sheets": _row_get(row, f"{prefix}_clean_sheets"),
        "goals_conceded": _row_get(row, f"{prefix}_goals_conceded"),
        "defensive_contribution": _row_get(row, f"{prefix}_defensive_contribution"),
        "tackles": _row_get(row, f"{prefix}_tackles"),
        "clearances_blocks_interceptions": _row_get(
            row, f"{prefix}_clearances_blocks_interceptions"
        ),
        "expected_goals": _row_get(row, f"{prefix}_expected_goals"),
        "expected_assists": _row_get(row, f"{prefix}_expected_assists"),
        "expected_goal_involvements": _row_get(row, f"{prefix}_expected_goal_involvements"),
        "saves": _row_get(row, f"{prefix}_saves"),
        "penalties_saved": _row_get(row, f"{prefix}_penalties_saved"),
        "bonus": _row_get(row, f"{prefix}_bonus"),
        "ict_index": _row_get(row, f"{prefix}_ict_index"),
        "yellow_cards": _row_get(row, f"{prefix}_yellow_cards"),
        "red_cards": _row_get(row, f"{prefix}_red_cards"),
        "points_per_game": _row_get(row, f"{prefix}_points_per_game"),
        "now_cost": _row_get(row, f"{prefix}_now_cost"),
        "web_name": _row_get(row, f"{prefix}_web_name"),
    }


def _as_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _compact_history(block: dict[str, Any] | None) -> dict[str, Any] | None:
    if not block:
        return None
    return {key: block.get(key) for key in HISTORY_COMPACT_FIELDS}


def player_from_row(row: pd.Series) -> PlayerView:
    player_id = int(_row_get(row, "id", "player_id"))
    element_type = int(_row_get(row, "element_type") or 1)
    now_cost = int(_row_get(row, "now_cost") or 0)
    position_name = _row_get(row, "position_name")
    position = ELEMENT_TYPE_TO_POSITION.get(element_type)
    if position is None and isinstance(position_name, str):
        mapping = {
            "Goalkeeper": "GK",
            "Defender": "DEF",
            "Midfielder": "MID",
            "Forward": "FWD",
        }
        position = mapping.get(position_name, "MID")
    return PlayerView(
        player_id=player_id,
        web_name=str(_row_get(row, "web_name") or ""),
        first_name=_row_get(row, "first_name"),
        second_name=_row_get(row, "second_name"),
        team_id=int(_row_get(row, "team") or _row_get(row, "team_id") or 0),
        team_name=str(_row_get(row, "team_name") or ""),
        position=position or "MID",
        element_type=element_type,
        now_cost=now_cost,
        price=float(_row_get(row, "price_millions") or tenths_to_millions(now_cost) or 0),
        status=_row_get(row, "status"),
        news=_row_get(row, "news"),
        chance_of_playing_this_round=_row_get(row, "chance_of_playing_this_round"),
        chance_of_playing_next_round=_row_get(row, "chance_of_playing_next_round"),
        can_select=_bool(_row_get(row, "can_select"), True),
        can_transact=_bool(_row_get(row, "can_transact"), True),
        removed=_bool(_row_get(row, "removed"), False),
        selected_by_percent=_row_get(row, "selected_by_percent"),
        form=_row_get(row, "form"),
        total_points=_row_get(row, "total_points"),
        event_points=_row_get(row, "event_points"),
        minutes=_row_get(row, "minutes"),
        starts=_row_get(row, "starts"),
        points_per_game=_row_get(row, "points_per_game"),
        ep_this=_row_get(row, "ep_this"),
        ep_next=_row_get(row, "ep_next"),
        goals_scored=_row_get(row, "goals_scored"),
        assists=_row_get(row, "assists"),
        clean_sheets=_row_get(row, "clean_sheets"),
        bonus=_row_get(row, "bonus"),
        goals_conceded=_row_get(row, "goals_conceded"),
        defensive_contribution=_row_get(row, "defensive_contribution"),
        tackles=_row_get(row, "tackles"),
        clearances_blocks_interceptions=_row_get(row, "clearances_blocks_interceptions"),
        expected_goals=_row_get(row, "expected_goals"),
        expected_assists=_row_get(row, "expected_assists"),
        expected_goal_involvements=_row_get(row, "expected_goal_involvements"),
        saves=_row_get(row, "saves"),
        penalties_saved=_row_get(row, "penalties_saved"),
        ict_index=_row_get(row, "ict_index"),
        yellow_cards=_row_get(row, "yellow_cards"),
        red_cards=_row_get(row, "red_cards"),
        transfers_in_event=_row_get(row, "transfers_in_event"),
        transfers_out_event=_row_get(row, "transfers_out_event"),
        history_2024_25=_history_block(row, "history_2024_25"),
        history_2023_24=_history_block(row, "history_2023_24"),
    )


class FPLWorldRepository:
    """Single implementation of the historical information boundary."""

    def __init__(self, world: HistoricalCSVWorld, context: WorldContext) -> None:
        self.world = world
        self.context = context
        self._player_cache: dict[int, PlayerView] | None = None
        self._player_cache_key: tuple[int, str] | None = None
        self._prior_history_cache: dict[int, dict[str, dict[str, Any] | None]] | None = None

    def bind(self, context: WorldContext) -> FPLWorldRepository:
        return FPLWorldRepository(self.world, context)

    def set_context(self, context: WorldContext) -> None:
        self.context = context
        self._player_cache = None
        self._player_cache_key = None

    @property
    def current_gw(self) -> int:
        return self.context.current_gw

    @property
    def latest_completed_gw(self) -> int | None:
        return self.context.latest_completed_gw

    def _assert_performance_gw_allowed(self, gw: int) -> None:
        latest = self.latest_completed_gw
        if latest is None or gw > latest:
            raise PermissionError(
                f"Performance for GW{gw} is not visible in {self.context.phase} GW{self.current_gw}"
            )

    def _assert_snapshot_gw_allowed(self, gw: int) -> None:
        if gw != self.current_gw:
            raise PermissionError(
                f"Player/fixture snapshot GW{gw} is not the current deadline GW{self.current_gw}"
            )

    def current_players(self) -> list[PlayerView]:
        frame = self.world.player_snapshot(self.current_gw)
        return [self._with_prior_history(player_from_row(row)) for _, row in frame.iterrows()]

    def _prior_season_index(self) -> dict[int, dict[str, dict[str, Any] | None]]:
        if self._prior_history_cache is not None:
            return self._prior_history_cache
        frame = self.world.player_snapshot(1)
        index: dict[int, dict[str, dict[str, Any] | None]] = {}
        for _, row in frame.iterrows():
            player = player_from_row(row)
            hist_24 = dict(player.history_2024_25) if player.history_2024_25 else None
            if hist_24 is not None:
                for key in PRIOR_DEFENSIVE_FIELDS:
                    if hist_24.get(key) is None:
                        hist_24[key] = getattr(player, key)
            index[player.player_id] = {
                "2024_25": hist_24,
                "2023_24": player.history_2023_24,
            }
        self._prior_history_cache = index
        return index

    def _with_prior_history(self, player: PlayerView) -> PlayerView:
        prior = self._prior_season_index().get(player.player_id)
        if not prior:
            return player
        hist_24 = player.history_2024_25
        if hist_24 is None:
            hist_24 = prior.get("2024_25")
        elif self.current_gw == 1:
            hist_24 = dict(hist_24)
            for key in PRIOR_DEFENSIVE_FIELDS:
                if hist_24.get(key) is None:
                    hist_24[key] = getattr(player, key)
        hist_23 = player.history_2023_24 or prior.get("2023_24")
        if hist_24 == player.history_2024_25 and hist_23 == player.history_2023_24:
            return player
        return player.model_copy(update={"history_2024_25": hist_24, "history_2023_24": hist_23})

    def _metric(
        self, player: PlayerView, sort_by: str, season: str
    ) -> tuple[float, str]:
        if sort_by in {"price", "now_cost"}:
            return float(player.price), "current"
        if season in {"current", ""}:
            return _as_float(getattr(player, sort_by, None)), "current"
        hist_key = "2023_24" if season == "2023_24" else "2024_25"
        hist = player.history_2024_25 if hist_key == "2024_25" else player.history_2023_24
        if isinstance(hist, dict) and hist.get(sort_by) is not None:
            return _as_float(hist.get(sort_by)), hist_key
        return 0.0, hist_key

    def search_players(
        self,
        *,
        query: str | None = None,
        position: str | None = None,
        team_id: int | None = None,
        team_name: str | None = None,
        max_price: float | None = None,
        min_price: float | None = None,
        status: str | None = None,
        sort_by: str = "total_points",
        season: str = "current",
        min_minutes: float | None = None,
        limit: int = 25,
    ) -> list[PlayerView]:
        players = self.current_players()
        query_l = query.lower().strip() if query else None
        pos = position.upper() if position else None
        team_l = team_name.lower() if team_name else None
        results: list[PlayerView] = []
        for player in players:
            if pos and player.position != pos:
                continue
            if team_id is not None and player.team_id != int(team_id):
                continue
            if team_l and team_l not in player.team_name.lower():
                continue
            if max_price is not None and player.price > float(max_price) + 1e-9:
                continue
            if min_price is not None and player.price < float(min_price) - 1e-9:
                continue
            if status and (player.status or "") != status:
                continue
            if query_l:
                hay = " ".join(
                    str(x)
                    for x in (
                        player.web_name,
                        player.first_name,
                        player.second_name,
                        player.team_name,
                    )
                    if x
                ).lower()
                if query_l not in hay:
                    continue
            if min_minutes is not None:
                minutes_val, _src = self._metric(player, "minutes", season)
                if minutes_val < float(min_minutes):
                    continue
            results.append(player)
        ascending = sort_by in ASCENDING_SORT

        def _sort_key(player: PlayerView) -> tuple[Any, ...]:
            value, _src = self._metric(player, sort_by, season)
            if ascending:
                return (value, player.price, player.web_name)
            return (-value, -(player.total_points or 0), player.price, player.web_name)

        results.sort(key=_sort_key)
        return results[: max(1, min(int(limit), 50))]

    def current_player_map(self) -> dict[int, PlayerView]:
        key = (self.current_gw, self.context.phase)
        if self._player_cache is None or self._player_cache_key != key:
            self._player_cache = {p.player_id: p for p in self.current_players()}
            self._player_cache_key = key
        return self._player_cache

    def get_player(self, player_id: int) -> PlayerView | None:
        return self.current_player_map().get(int(player_id))

    def current_fixtures(self, team_id: int | None = None, next_n: int | None = 5) -> list[dict[str, Any]]:
        frame = self.world.fixtures_snapshot(self.current_gw)
        rows = []
        for _, row in frame.iterrows():
            record = {col: _clean(row[col]) for col in frame.columns}
            if team_id is not None:
                if int(record.get("home_team_id") or 0) != int(team_id) and int(
                    record.get("away_team_id") or 0
                ) != int(team_id):
                    continue
            rows.append(record)
        if team_id is not None and next_n is not None:
            assigned = [r for r in rows if r.get("assigned_gw") not in (None, "")]
            assigned.sort(key=lambda r: int(r["assigned_gw"]))
            unassigned = [r for r in rows if r.get("assigned_gw") in (None, "")]
            return assigned[: int(next_n)] + unassigned
        return rows

    def current_standings(self) -> list[dict[str, Any]]:
        frame = self.world.standings_snapshot(self.current_gw)
        if frame.empty:
            return []
        return [{col: _clean(row[col]) for col in frame.columns} for _, row in frame.iterrows()]

    def past_results(self, team_id: int | None = None) -> list[dict[str, Any]]:
        latest = self.latest_completed_gw
        if latest is None:
            return []
        frame = self.world.results_through(latest)
        rows = []
        for _, row in frame.iterrows():
            gw = int(_clean(row["gameweek"]))
            if gw > latest:
                continue
            record = {col: _clean(row[col]) for col in frame.columns}
            if team_id is not None:
                if int(record.get("home_team_id") or 0) != int(team_id) and int(
                    record.get("away_team_id") or 0
                ) != int(team_id):
                    continue
            rows.append(record)
        return rows

    def player_performance(self, player_id: int, last_n: int | None = None) -> list[dict[str, Any]]:
        latest = self.latest_completed_gw
        if latest is None:
            return []
        rows: list[dict[str, Any]] = []
        for gw in range(1, latest + 1):
            frame = self.world.player_performance(gw)
            match = frame[frame["player_id"] == int(player_id)]
            if match.empty:
                continue
            row = match.iloc[0]
            rows.append(
                {
                    "gameweek": gw,
                    "player_id": int(player_id),
                    "player_name": _clean(row.get("player_name")),
                    "minutes": _clean(row.get("minutes")),
                    "starts": _clean(row.get("starts")),
                    "goals_scored": _clean(row.get("goals_scored")),
                    "assists": _clean(row.get("assists")),
                    "clean_sheets": _clean(row.get("clean_sheets")),
                    "bonus": _clean(row.get("bonus")),
                    "total_points": _clean(row.get("total_points")),
                    "team_fixtures_in_gameweek": _clean(row.get("team_fixtures_in_gameweek")),
                    "expected_goals": _clean(row.get("expected_goals")),
                    "expected_assists": _clean(row.get("expected_assists")),
                }
            )
        if last_n is not None:
            rows = rows[-int(last_n) :]
        return rows

    def player_fixture_history(self, player_id: int, last_n: int | None = None) -> list[dict[str, Any]]:
        latest = self.latest_completed_gw
        if latest is None:
            return []
        rows: list[dict[str, Any]] = []
        for gw in range(1, latest + 1):
            frame = self.world.player_fixture_stats(gw)
            match = frame[frame["player_id"] == int(player_id)]
            for _, row in match.iterrows():
                rows.append(
                    {
                        "gameweek": gw,
                        "fixture_id": _clean(row.get("fixture_id")),
                        "kickoff_time": _clean(row.get("kickoff_time")),
                        "opponent_team_name": _clean(row.get("opponent_team_name")),
                        "venue": _clean(row.get("venue")),
                        "did_play": _bool(row.get("did_play"), False),
                        "minutes": _clean(row.get("minutes")),
                        "fixture_fpl_points": _clean(row.get("fixture_fpl_points")),
                        "goals_scored": _clean(row.get("goals_scored")),
                        "assists": _clean(row.get("assists")),
                        "clean_sheets": _clean(row.get("clean_sheets")),
                        "bonus": _clean(row.get("bonus")),
                    }
                )
        if last_n is not None:
            rows = rows[-int(last_n) :]
        return rows

    def gw_performance_map(self, gw: int) -> dict[int, dict[str, Any]]:
        self._assert_performance_gw_allowed(gw)
        frame = self.world.player_performance(gw)
        out: dict[int, dict[str, Any]] = {}
        for _, row in frame.iterrows():
            pid = int(row["player_id"])
            out[pid] = {
                "player_id": pid,
                "minutes": int(_clean(row.get("minutes")) or 0),
                "total_points": int(_clean(row.get("total_points")) or 0),
                "starts": int(_clean(row.get("starts")) or 0),
            }
        return out

    def historical_results(
        self,
        team_id: int | None = None,
        season: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        frame = self.world.historical_results()
        rows = []
        for _, row in frame.iterrows():
            record = {col: _clean(row[col]) for col in frame.columns}
            if season and str(record.get("season")) != str(season):
                continue
            if team_id is not None:
                home = record.get("home_team_2025_26_id")
                away = record.get("away_team_2025_26_id")
                ids = [int(x) for x in (home, away) if x not in (None, "")]
                if int(team_id) not in ids:
                    continue
            rows.append(record)
        return rows[: max(1, min(int(limit), 50))]

    def awards(self) -> list[dict[str, Any]]:
        latest = self.latest_completed_gw
        if latest is None:
            return []
        frame = self.world.awards()
        rows = []
        for _, row in frame.iterrows():
            gw = int(_clean(row["gameweek"]))
            if gw > latest:
                continue
            rows.append({col: _clean(row[col]) for col in frame.columns})
        return rows

    def awards_for_gw(self, gw: int) -> dict[str, Any] | None:
        latest = self.latest_completed_gw
        if latest is None or gw > latest:
            return None
        frame = self.world.awards()
        match = frame[frame["gameweek"] == int(gw)]
        if match.empty:
            return None
        return {col: _clean(match.iloc[0][col]) for col in frame.columns}

    def chip_usage(self) -> list[dict[str, Any]]:
        latest = self.latest_completed_gw
        if latest is None:
            return []
        frame = self.world.chip_usage()
        rows = []
        for _, row in frame.iterrows():
            gw = int(_clean(row["gameweek"]))
            if gw > latest:
                continue
            rows.append({col: _clean(row[col]) for col in frame.columns})
        return rows

    def totw(self, gw: int | None = None) -> list[dict[str, Any]]:
        latest = self.latest_completed_gw
        if latest is None:
            return []
        if gw is not None and gw > latest:
            return []
        frame = self.world.totw(gw)
        rows = []
        for _, row in frame.iterrows():
            row_gw = int(_clean(row["gameweek"]))
            if row_gw > latest:
                continue
            rows.append({col: _clean(row[col]) for col in frame.columns})
        return rows

    def top_performers(
        self,
        last_n: int = 1,
        position: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        latest = self.latest_completed_gw
        if latest is None:
            return []
        start = max(1, latest - int(last_n) + 1)
        totals: dict[int, dict[str, Any]] = {}
        for gw in range(start, latest + 1):
            frame = self.world.player_performance(gw)
            for _, row in frame.iterrows():
                pid = int(row["player_id"])
                pos_name = _clean(row.get("position_name"))
                if position:
                    mapping = {
                        "GK": "Goalkeeper",
                        "DEF": "Defender",
                        "MID": "Midfielder",
                        "FWD": "Forward",
                    }
                    wanted = mapping.get(position.upper(), position)
                    if pos_name != wanted:
                        continue
                entry = totals.setdefault(
                    pid,
                    {
                        "player_id": pid,
                        "player_name": _clean(row.get("player_name")),
                        "team_name": _clean(row.get("team_name")),
                        "position_name": pos_name,
                        "total_points": 0,
                        "minutes": 0,
                    },
                )
                entry["total_points"] += int(_clean(row.get("total_points")) or 0)
                entry["minutes"] += int(_clean(row.get("minutes")) or 0)
        ranked = sorted(totals.values(), key=lambda r: r["total_points"], reverse=True)
        return ranked[: max(1, min(int(limit), 25))]

    def compact_player(
        self,
        player: PlayerView,
        *,
        sort_by: str | None = None,
        season: str | None = None,
        sort_value: float | None = None,
    ) -> dict[str, Any]:
        data = player.model_dump(include=set(COMPACT_PLAYER_FIELDS))
        prior = _compact_history(player.history_2024_25)
        if prior:
            data["history_2024_25"] = prior
        if sort_by:
            data["sort_by"] = sort_by
            data["season"] = season
            data["sort_value"] = sort_value
        return data
