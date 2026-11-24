from __future__ import annotations

from fpl_sim.simulator.chip_validation import validate_chip
from fpl_sim.simulator.lineup_validation import validate_lineup
from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.simulator.squad_validation import validate_initial_squad
from fpl_sim.simulator.transfer_validation import validate_transfers
from fpl_sim.types import PlayerView, TransferMove, ValidationResult


class FPLRulesEngine:
    def __init__(self, rules: Ruleset | None = None) -> None:
        self.rules = rules or Ruleset.load()

    def validate_initial_squad(
        self,
        player_ids: list[int],
        players: dict[int, PlayerView],
        budget_tenths: int | None = None,
    ) -> ValidationResult:
        return validate_initial_squad(player_ids, players, self.rules, budget_tenths)

    def validate_lineup(
        self,
        squad_ids: list[int],
        starters: list[int],
        bench_outfield: list[int],
        reserve_gk: int,
        captain_id: int,
        vice_captain_id: int,
        players: dict[int, PlayerView],
    ) -> ValidationResult:
        return validate_lineup(
            squad_ids,
            starters,
            bench_outfield,
            reserve_gk,
            captain_id,
            vice_captain_id,
            players,
            self.rules,
        )

    def validate_transfers(
        self,
        current_ids: list[int],
        moves: list[TransferMove],
        players: dict[int, PlayerView],
        purchase_prices: dict[int, int],
        bank_tenths: int,
        free_transfers: int,
        chip_type: str | None = None,
    ) -> ValidationResult:
        return validate_transfers(
            current_ids,
            moves,
            players,
            purchase_prices,
            bank_tenths,
            free_transfers,
            self.rules,
            chip_type,
        )

    def validate_chip(
        self,
        chip_type: str,
        current_gw: int,
        entitlements: list[dict],
        already_selected: str | None = None,
    ) -> ValidationResult:
        return validate_chip(
            chip_type, current_gw, entitlements, already_selected, self.rules
        )
