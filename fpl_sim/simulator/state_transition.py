from __future__ import annotations

from fpl_sim.simulator.pricing import next_free_transfers, selling_price_tenths
from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.types import PlayerView, SquadMember


def refresh_selling_prices(
    members: list[SquadMember],
    players: dict[int, PlayerView],
) -> list[SquadMember]:
    refreshed: list[SquadMember] = []
    for member in members:
        current = players[member.player_id].now_cost
        refreshed.append(
            member.model_copy(
                update={
                    "selling_price_tenths": selling_price_tenths(
                        member.purchase_price_tenths, current
                    )
                }
            )
        )
    return refreshed


def accrue_free_transfers(stored: int, rules: Ruleset, chip_type: str | None = None) -> int:
    # Wildcard / Free Hit do not reset stored FTs; weekly accrual still applies.
    return next_free_transfers(stored, rules.weekly_accrual, rules.max_free_transfers)


def members_from_ids(
    player_ids: list[int],
    players: dict[int, PlayerView],
    purchase_prices: dict[int, int] | None = None,
    starters: list[int] | None = None,
    bench_outfield: list[int] | None = None,
    reserve_gk: int | None = None,
    captain_id: int | None = None,
    vice_captain_id: int | None = None,
) -> list[SquadMember]:
    members: list[SquadMember] = []
    for pid in player_ids:
        purchase = (purchase_prices or {}).get(pid, players[pid].now_cost)
        selling = selling_price_tenths(purchase, players[pid].now_cost)
        is_starter = bool(starters and pid in starters)
        bench_order = None
        if bench_outfield and pid in bench_outfield:
            bench_order = bench_outfield.index(pid) + 1
        members.append(
            SquadMember(
                player_id=pid,
                purchase_price_tenths=purchase,
                selling_price_tenths=selling,
                is_starter=is_starter,
                bench_order=bench_order,
                is_captain=pid == captain_id,
                is_vice_captain=pid == vice_captain_id,
                is_reserve_gk=pid == reserve_gk,
            )
        )
    return members
