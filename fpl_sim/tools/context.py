from __future__ import annotations

from typing import Any

from fpl_sim.simulator.pricing import selling_price_tenths
from fpl_sim.simulator.rules import FPLRulesEngine
from fpl_sim.simulator.state_transition import members_from_ids
from fpl_sim.types import PendingDecision, SessionStats, TransferMove, ValidationResult, tenths_to_millions
from fpl_sim.world.repository import FPLWorldRepository, SEARCH_SORT_FIELDS


def _ok(result: ValidationResult) -> dict[str, Any]:
    payload: dict[str, Any] = {"accepted": result.accepted, "errors": result.errors}
    payload.update(result.data)
    return payload


class ToolContext:
    def __init__(
        self,
        repo: FPLWorldRepository,
        rules: FPLRulesEngine,
        pending: PendingDecision,
        stats: SessionStats,
        manager_state: dict[str, Any],
        entitlements: list[dict[str, Any]],
        gw1: bool = False,
    ) -> None:
        self.repo = repo
        self.rules = rules
        self.pending = pending
        self.stats = stats
        self.manager_state = manager_state
        self.entitlements = entitlements
        self.gw1 = gw1
        self.finalized = False

    def _note_invalid(self, result: ValidationResult) -> dict[str, Any]:
        if not result.accepted:
            self.stats.invalid_actions += 1
        return _ok(result)

    def _reject(self, *errors: str) -> dict[str, Any]:
        self.stats.invalid_actions += 1
        return {"accepted": False, "errors": [e for e in errors if e]}

    def _locked_error(self) -> dict[str, Any] | None:
        if self.finalized:
            return self._reject("This Gameweek is already locked by submit_lineup.")
        return None

    def search_players(
        self,
        query: str | None = None,
        position: str | None = None,
        team_name: str | None = None,
        team_id: int | None = None,
        max_price: float | None = None,
        min_price: float | None = None,
        status: str | None = None,
        sort_by: str = "total_points",
        season: str = "current",
        min_minutes: float | None = None,
        limit: int = 15,
    ) -> dict[str, Any]:
        sort_key = (sort_by or "total_points").strip()
        season_key = (season or "current").strip()
        if season_key == "prior":
            season_key = "2024_25"
        if sort_key not in SEARCH_SORT_FIELDS:
            return {
                "accepted": False,
                "errors": [
                    f"Unknown sort_by '{sort_key}'. Use one of: {', '.join(SEARCH_SORT_FIELDS)}"
                ],
            }
        if season_key not in {"current", "2024_25", "2023_24"}:
            return {
                "accepted": False,
                "errors": [
                    "season must be current, 2024_25 (alias: prior), or 2023_24."
                ],
            }
        players = self.repo.search_players(
            query=query,
            position=position,
            team_name=team_name,
            team_id=team_id,
            max_price=max_price,
            min_price=min_price,
            status=status,
            sort_by=sort_key,
            season=season_key,
            min_minutes=min_minutes,
            limit=limit,
        )
        rows = []
        for player in players:
            value, source = self.repo._metric(player, sort_key, season_key)
            rows.append(
                self.repo.compact_player(
                    player,
                    sort_by=sort_key,
                    season=source,
                    sort_value=value,
                )
            )
        payload: dict[str, Any] = {
            "players": rows,
            "count": len(rows),
            "sort_by": sort_key,
            "season": season_key,
        }
        if self.gw1 and season_key == "current":
            payload["note"] = (
                "GW1 current-snapshot totals are last season's counting stats "
                "(points, minutes, DC, xG). Use season=2024_25 to rank the nested prior-season block."
            )
        elif season_key != "current" and self.repo.current_gw > 1:
            payload["note"] = (
                "Prior-season stats are attached from the GW1 profiles; "
                "current-snapshot fields are 2025/26 season-to-date."
            )
        return payload

    def get_player(self, player_id: int) -> dict[str, Any]:
        player = self.repo.get_player(int(player_id))
        if player is None:
            return {"accepted": False, "errors": [f"Player {player_id} is not in the current pool."]}
        return {"player": player.model_dump()}

    def compare_players(self, player_ids: list[int]) -> dict[str, Any]:
        found = []
        missing = []
        for pid in player_ids[:6]:
            player = self.repo.get_player(int(pid))
            if player is None:
                missing.append(int(pid))
            else:
                found.append(self.repo.compact_player(player))
        return {"players": found, "missing": missing}

    def get_player_performance(self, player_id: int, last_n: int = 5) -> dict[str, Any]:
        return {
            "player_id": int(player_id),
            "latest_completed_gw": self.repo.latest_completed_gw,
            "performances": self.repo.player_performance(int(player_id), last_n=int(last_n)),
        }

    def get_player_fixture_history(self, player_id: int, last_n: int = 5) -> dict[str, Any]:
        return {
            "player_id": int(player_id),
            "fixtures": self.repo.player_fixture_history(int(player_id), last_n=int(last_n)),
        }

    def get_team_fixtures(self, team_id: int, next_n: int = 5) -> dict[str, Any]:
        return {
            "team_id": int(team_id),
            "fixtures": self.repo.current_fixtures(int(team_id), int(next_n)),
        }

    def get_team_results(self, team_id: int) -> dict[str, Any]:
        return {"team_id": int(team_id), "results": self.repo.past_results(int(team_id))}

    def get_standings(self) -> dict[str, Any]:
        rows = self.repo.current_standings()
        if not rows:
            return {"standings": [], "note": "No league table is available before GW1 is played."}
        return {"standings": rows}

    def get_historical_results(
        self,
        team_id: int | None = None,
        season: str | None = None,
        limit: int = 15,
    ) -> dict[str, Any]:
        return {"results": self.repo.historical_results(team_id=team_id, season=season, limit=limit)}

    def get_top_performers(
        self, last_n: int = 1, position: str | None = None, limit: int = 10
    ) -> dict[str, Any]:
        return {
            "latest_completed_gw": self.repo.latest_completed_gw,
            "performers": self.repo.top_performers(last_n=last_n, position=position, limit=limit),
        }

    def get_manager_state(self) -> dict[str, Any]:
        return {
            "current_gw": self.repo.current_gw,
            "phase": self.repo.context.phase,
            "bank": tenths_to_millions(
                self.manager_state.get("draft_bank_tenths", self.manager_state.get("bank_tenths", 0))
            ),
            "free_transfers": self.manager_state.get("free_transfers"),
            "team_value": tenths_to_millions(self.manager_state.get("team_value_tenths")),
            "total_points": self.manager_state.get("total_points", 0),
            "pending_chip": self.pending.chip_type,
            "pending_transfers": [m.model_dump() for m in self.pending.transfers],
            "squad": self._squad_rows(),
            "starters": self.pending.starters,
            "bench_outfield": self.pending.bench_outfield,
            "reserve_gk": self.pending.reserve_gk,
            "captain_id": self.pending.captain_id,
            "vice_captain_id": self.pending.vice_captain_id,
            "chips": self._chips_for_gw(),
        }

    def _squad_rows(self) -> list[dict[str, Any]]:
        players = self.repo.current_player_map()
        squad_ids = self.pending.player_ids or self.manager_state.get("player_ids") or []
        purchases = dict(
            self.manager_state.get("draft_purchase_prices")
            or self.manager_state.get("purchase_prices")
            or {}
        )
        selling_by_id = {
            m.player_id: m.selling_price_tenths for m in (self.pending.members or [])
        }
        rows = []
        for pid in squad_ids:
            player = players.get(int(pid))
            if not player:
                continue
            row = self.repo.compact_player(player)
            purchase = int(purchases.get(int(pid), player.now_cost))
            sell = selling_by_id.get(int(pid), selling_price_tenths(purchase, player.now_cost))
            row["selling_price"] = tenths_to_millions(sell)
            rows.append(row)
        return rows

    def _chips_for_gw(self) -> list[dict[str, Any]]:
        gw = int(self.repo.current_gw)
        rows = []
        for c in self.entitlements:
            used = c.get("used_gw")
            if used not in (None, "") and int(used) != gw:
                continue
            if int(c["available_from_gw"]) <= gw <= int(c["expires_after_gw"]):
                rows.append(
                    {
                        "chip_type": c["chip_type"],
                        "available_from_gw": c["available_from_gw"],
                        "expires_after_gw": c["expires_after_gw"],
                        "used_gw": used,
                    }
                )
        return rows

    def submit_initial_squad(self, player_ids: list[int]) -> dict[str, Any]:
        locked = self._locked_error()
        if locked:
            return locked
        if not self.gw1:
            return self._reject(
                "GW1 already passed. Call submit_transfers to change the squad, then submit_lineup to lock."
            )
        players = self.repo.current_player_map()
        result = self.rules.validate_initial_squad(player_ids, players)
        if result.accepted:
            self.pending.player_ids = [int(x) for x in player_ids]
            self.pending.members = members_from_ids(self.pending.player_ids, players)
            self.manager_state["bank_tenths"] = result.data["bank_tenths"]
            result.data["bank"] = tenths_to_millions(result.data["bank_tenths"])
            result.data["message"] = "Squad accepted (draft). Call submit_lineup to lock this Gameweek."
        return self._note_invalid(result)

    def submit_transfers(self, transfers: list[dict[str, Any]]) -> dict[str, Any]:
        locked = self._locked_error()
        if locked:
            return locked
        if self.gw1:
            return self._reject(
                "GW1 uses submit_initial_squad, not transfers. "
                "Call submit_initial_squad with 15 player_ids, then submit_lineup to lock."
            )
        base_ids = list(self.manager_state.get("player_ids") or [])
        if not base_ids:
            return self._reject("No locked squad. Finish GW1 with submit_initial_squad and submit_lineup first.")
        if self.pending.chip_type == "freehit" and self.pending.free_hit_base_player_ids:
            base_ids = list(self.pending.free_hit_base_player_ids)
        players = self.repo.current_player_map()
        purchases = dict(self.manager_state.get("purchase_prices") or {})
        moves = [
            TransferMove(player_out_id=int(t["player_out_id"]), player_in_id=int(t["player_in_id"]))
            for t in transfers
        ]
        result = self.rules.validate_transfers(
            base_ids,
            moves,
            players,
            purchases,
            int(self.manager_state.get("bank_tenths") or 0),
            int(self.manager_state.get("free_transfers") or 0),
            self.pending.chip_type,
        )
        if result.accepted:
            self.pending.transfers = [TransferMove(**m) for m in result.data["moves"]]
            self.pending.player_ids = result.data["player_ids"]
            self.pending.members = members_from_ids(
                self.pending.player_ids,
                players,
                result.data["purchase_prices"],
            )
            self.manager_state["draft_bank_tenths"] = result.data["bank_tenths"]
            self.manager_state["draft_purchase_prices"] = result.data["purchase_prices"]
            result.data["bank"] = tenths_to_millions(result.data["bank_tenths"])
            result.data["hit"] = result.data["transfer_hit"]
            result.data["message"] = "Transfers accepted (draft until submit_lineup locks this Gameweek)."
        return self._note_invalid(result)

    def submit_lineup(
        self,
        starters: list[int],
        bench_outfield: list[int],
        reserve_gk: int,
        captain_id: int,
        vice_captain_id: int,
    ) -> dict[str, Any]:
        locked = self._locked_error()
        if locked:
            return locked
        squad_ids = self.pending.player_ids or self.manager_state.get("player_ids") or []
        if not squad_ids:
            if self.gw1:
                return self._reject(
                    "Call submit_initial_squad first with 15 player_ids, then submit_lineup to lock this Gameweek."
                )
            return self._reject("No squad is available. Call submit_transfers if you need to change it, then submit_lineup.")
        players = self.repo.current_player_map()
        result = self.rules.validate_lineup(
            squad_ids,
            starters,
            bench_outfield,
            reserve_gk,
            captain_id,
            vice_captain_id,
            players,
        )
        if result.accepted:
            self.pending.starters = [int(x) for x in starters]
            self.pending.bench_outfield = [int(x) for x in bench_outfield]
            self.pending.reserve_gk = int(reserve_gk)
            self.pending.captain_id = int(captain_id)
            self.pending.vice_captain_id = int(vice_captain_id)
            self.finalized = True
            result.data["message"] = "Lineup accepted. This Gameweek is locked."
        return self._note_invalid(result)

    def play_chip(self, chip_type: str) -> dict[str, Any]:
        locked = self._locked_error()
        if locked:
            return locked
        result = self.rules.validate_chip(
            chip_type,
            self.repo.current_gw,
            self.entitlements,
            self.pending.chip_type,
        )
        if result.accepted:
            if chip_type == "freehit" and self.pending.free_hit_base_player_ids is None:
                self.pending.free_hit_base_player_ids = list(
                    self.manager_state.get("player_ids") or []
                )
            self.pending.chip_type = chip_type  # type: ignore[assignment]
        return self._note_invalid(result)
