from __future__ import annotations


def selling_price_tenths(purchase_tenths: int, current_tenths: int) -> int:
    """Official FPL sell price: keep half of a rise (rounded down 0.1), full drop."""
    purchase = int(purchase_tenths)
    current = int(current_tenths)
    if current >= purchase:
        return purchase + (current - purchase) // 2
    return current


def team_value_tenths(selling_prices: list[int], bank_tenths: int) -> int:
    return int(sum(selling_prices) + bank_tenths)


def next_free_transfers(stored: int, accrual: int = 1, cap: int = 5) -> int:
    return min(int(cap), int(stored) + int(accrual))


def transfer_hit(n_transfers: int, free_transfers: int, hit_cost: int = -4) -> tuple[int, int, int]:
    """Return (paid_transfers, hit_points, remaining_fts)."""
    used_free = min(int(n_transfers), int(free_transfers))
    paid = max(0, int(n_transfers) - int(free_transfers))
    remaining = int(free_transfers) - used_free
    return paid, paid * int(hit_cost), remaining
