from __future__ import annotations

from collections import Counter

from fpl_sim.simulator.pricing import selling_price_tenths, transfer_hit
from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.types import PlayerView, TransferMove, ValidationResult


def validate_transfers(
    current_ids: list[int],
    moves: list[TransferMove],
    players: dict[int, PlayerView],
    purchase_prices: dict[int, int],
    bank_tenths: int,
    free_transfers: int,
    rules: Ruleset,
    chip_type: str | None = None,
) -> ValidationResult:
    errors: list[str] = []
    squad = [int(x) for x in current_ids]
    if not moves:
        return ValidationResult.ok(
            player_ids=squad,
            bank_tenths=bank_tenths,
            n_transfers=0,
            paid_transfers=0,
            transfer_hit=0,
            remaining_fts=free_transfers,
            moves=[],
        )

    outs = [int(m.player_out_id) for m in moves]
    ins = [int(m.player_in_id) for m in moves]
    if len(set(outs)) != len(outs):
        errors.append("A player cannot be transferred out more than once in one batch.")
    if len(set(ins)) != len(ins):
        errors.append("A player cannot be transferred in more than once in one batch.")
    if set(outs) & set(ins):
        errors.append("The same player cannot be transferred in and out in one batch.")

    for pid in outs:
        if pid not in squad:
            errors.append(f"Cannot transfer out player {pid}: not in the current squad.")
    for pid in ins:
        if pid in squad and pid not in outs:
            errors.append(f"Cannot transfer in player {pid}: already in the squad.")
        player = players.get(pid)
        if player is None:
            errors.append(f"Player {pid} is not in the current selectable pool.")
        elif not player.can_select or player.removed or not player.can_transact:
            errors.append(f"{player.web_name} cannot be transferred in at this deadline.")

    if errors:
        return ValidationResult.fail(*errors)

    priced: list[TransferMove] = []
    new_squad = list(squad)
    new_bank = int(bank_tenths)
    new_purchases = dict(purchase_prices)
    for move in moves:
        out_id, in_id = int(move.player_out_id), int(move.player_in_id)
        out_player = players[out_id]
        in_player = players[in_id]
        sell = selling_price_tenths(int(purchase_prices[out_id]), out_player.now_cost)
        buy = in_player.now_cost
        new_bank += sell - buy
        new_squad.remove(out_id)
        new_squad.append(in_id)
        new_purchases.pop(out_id, None)
        new_purchases[in_id] = buy
        priced.append(
            TransferMove(
                player_out_id=out_id,
                player_in_id=in_id,
                sell_price_tenths=sell,
                buy_price_tenths=buy,
            )
        )

    if new_bank < 0:
        errors.append(
            f"Transfers would leave the bank at £{new_bank / 10:.1f}m. Bank cannot go negative."
        )

    new_players = [players[pid] for pid in new_squad]
    pos_counts = Counter(p.position for p in new_players)
    for pos, needed in rules.squad_positions.items():
        if pos_counts.get(pos, 0) != needed:
            errors.append(f"After transfers the squad has {pos_counts.get(pos, 0)} {pos}, needs {needed}.")

    club_counts = Counter(p.team_id for p in new_players)
    over = [players[pid].team_name for pid in new_squad if club_counts[players[pid].team_id] > rules.max_per_club]
    over = sorted(set(over))
    if over:
        errors.append(
            f"After transfers the squad still exceeds {rules.max_per_club} players for: {', '.join(over)}."
        )

    unlimited = chip_type in {"wildcard", "freehit"}
    if unlimited:
        paid, hit, remaining = 0, 0, int(free_transfers)
    else:
        paid, hit, remaining = transfer_hit(len(priced), free_transfers, rules.hit_cost)

    if chip_type is None and len(priced) > 0 and free_transfers == 0 and rules.gw1_free_transfers == 0:
        # GW1 has no transfers unless a later ruleset allows it.
        pass

    return ValidationResult(
        accepted=not errors,
        errors=errors,
        data={
            "player_ids": new_squad,
            "purchase_prices": new_purchases,
            "bank_tenths": new_bank,
            "n_transfers": len(priced),
            "paid_transfers": paid,
            "transfer_hit": hit,
            "remaining_fts": remaining,
            "moves": [m.model_dump() for m in priced],
        },
    )
