from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryStore:
    """In-process store used by tests. Same methods as SupabaseStore."""

    def __init__(self) -> None:
        self.simulations: dict[str, dict[str, Any]] = {}
        self.chips: dict[str, dict[str, Any]] = {}
        self.gameweeks: dict[str, dict[str, Any]] = {}
        self.squads: dict[str, list[dict[str, Any]]] = {}
        self.transfers: dict[str, dict[str, Any]] = {}
        self.points: dict[str, list[dict[str, Any]]] = {}

    def ping(self) -> bool:
        return True

    def wipe_all_simulations(self) -> int:
        n = len(self.simulations)
        self.simulations.clear()
        self.chips.clear()
        self.gameweeks.clear()
        self.squads.clear()
        self.transfers.clear()
        self.points.clear()
        return n

    def create_simulation(
        self,
        name: str,
        season: str,
        mode: str,
        config_name: str,
        mlflow_run_id: str | None,
        current_gw: int,
        chip_entitlements: list[dict[str, Any]],
    ) -> dict[str, Any]:
        sim_id = str(uuid4())
        sim = {
            "id": sim_id,
            "name": name,
            "season": season,
            "mode": mode,
            "config_name": config_name,
            "mlflow_run_id": mlflow_run_id,
            "status": "in_progress",
            "current_gw": current_gw,
            "total_points": 0,
            "created_at": _now(),
            "completed_at": None,
        }
        self.simulations[sim_id] = sim
        for ent in chip_entitlements:
            chip_id = str(uuid4())
            self.chips[chip_id] = {
                "id": chip_id,
                "simulation_id": sim_id,
                "used_gw": None,
                "created_at": _now(),
                **ent,
            }
        result = deepcopy(sim)
        result["chips"] = self.list_chips(sim_id)
        return result

    def get_simulation(self, simulation_id: str) -> dict[str, Any] | None:
        row = self.simulations.get(simulation_id)
        return deepcopy(row) if row else None

    def update_simulation(self, simulation_id: str, **fields: Any) -> dict[str, Any]:
        self.simulations[simulation_id].update(fields)
        return deepcopy(self.simulations[simulation_id])

    def list_chips(self, simulation_id: str) -> list[dict[str, Any]]:
        return deepcopy([c for c in self.chips.values() if c["simulation_id"] == simulation_id])

    def mark_chip_used(self, chip_id: str, used_gw: int) -> dict[str, Any]:
        self.chips[chip_id]["used_gw"] = used_gw
        return deepcopy(self.chips[chip_id])

    def upsert_gameweek(self, simulation_id: str, gw: int, **fields: Any) -> dict[str, Any]:
        existing = self.get_gameweek(simulation_id, gw)
        if existing:
            self.gameweeks[existing["id"]].update(fields)
            return deepcopy(self.gameweeks[existing["id"]])
        gw_id = str(uuid4())
        row = {
            "id": gw_id,
            "simulation_id": simulation_id,
            "gw": gw,
            "created_at": _now(),
            **fields,
        }
        self.gameweeks[gw_id] = row
        return deepcopy(row)

    def get_gameweek(self, simulation_id: str, gw: int) -> dict[str, Any] | None:
        for row in self.gameweeks.values():
            if row["simulation_id"] == simulation_id and row["gw"] == gw:
                return deepcopy(row)
        return None

    def get_gameweek_by_id(self, manager_gameweek_id: str) -> dict[str, Any] | None:
        row = self.gameweeks.get(manager_gameweek_id)
        return deepcopy(row) if row else None

    def replace_squad(self, manager_gameweek_id: str, players: list[dict[str, Any]]) -> None:
        rows = []
        for player in players:
            rows.append({"id": str(uuid4()), "manager_gameweek_id": manager_gameweek_id, **player})
        self.squads[manager_gameweek_id] = rows

    def list_squad(self, manager_gameweek_id: str) -> list[dict[str, Any]]:
        return deepcopy(self.squads.get(manager_gameweek_id, []))

    def add_transfers(
        self, manager_gameweek_id: str, transfers: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        rows = []
        for move in transfers:
            row = {
                "id": str(uuid4()),
                "manager_gameweek_id": manager_gameweek_id,
                "created_at": _now(),
                **move,
            }
            self.transfers[row["id"]] = row
            rows.append(row)
        return deepcopy(rows)

    def list_transfers(self, manager_gameweek_id: str) -> list[dict[str, Any]]:
        return deepcopy(
            [t for t in self.transfers.values() if t["manager_gameweek_id"] == manager_gameweek_id]
        )

    def replace_player_points(
        self, manager_gameweek_id: str, rows: list[dict[str, Any]]
    ) -> None:
        self.points[manager_gameweek_id] = [
            {"id": str(uuid4()), "manager_gameweek_id": manager_gameweek_id, **row} for row in rows
        ]

    def list_player_points(self, manager_gameweek_id: str) -> list[dict[str, Any]]:
        return deepcopy(self.points.get(manager_gameweek_id, []))
