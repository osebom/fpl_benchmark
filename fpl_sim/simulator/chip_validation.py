from __future__ import annotations

from typing import Any

from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.types import ValidationResult


def chip_is_eligible(chip: dict[str, Any], current_gw: int) -> bool:
    return (
        chip.get("used_gw") in (None, "")
        and int(chip["available_from_gw"]) <= current_gw <= int(chip["expires_after_gw"])
    )


def validate_chip(
    chip_type: str,
    current_gw: int,
    entitlements: list[dict[str, Any]],
    already_selected: str | None,
    rules: Ruleset,
) -> ValidationResult:
    errors: list[str] = []
    if chip_type not in {"wildcard", "freehit", "bboost", "3xc"}:
        return ValidationResult.fail(f"Unknown chip type: {chip_type}.")
    if already_selected and already_selected != chip_type:
        errors.append("Only one chip may be used per Gameweek.")
    matches = [
        c
        for c in entitlements
        if c["chip_type"] == chip_type and chip_is_eligible(c, current_gw)
    ]
    if not matches:
        errors.append(
            f"{chip_type} is not eligible in GW{current_gw} (wrong window or already used)."
        )
        return ValidationResult.fail(*errors)
    chosen = matches[0]
    return ValidationResult(
        accepted=not errors,
        errors=errors,
        data={"chip_type": chip_type, "entitlement_id": chosen.get("id")},
    )
