"""Optional helpers for compacting stored manager rows. Not used in the live lock path."""

from __future__ import annotations

from typing import Any


def compact_history(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"gw": r.get("gw"), "summary": r.get("summary")} for r in rows]
