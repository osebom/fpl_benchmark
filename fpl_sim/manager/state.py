"""Hard manager state lives in Supabase; this module is a convenience view."""

from __future__ import annotations

from typing import Any


def squad_ids(squad_rows: list[dict[str, Any]]) -> list[int]:
    return [int(row["player_id"]) for row in squad_rows]
