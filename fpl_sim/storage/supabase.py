from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from supabase import Client, create_client


def _normalize_supabase_url(url: str) -> str:
    cleaned = url.strip().strip('"').strip("'").rstrip("/")
    lower = cleaned.lower()
    if lower.endswith("/rest/v1"):
        cleaned = cleaned[: -len("/rest/v1")].rstrip("/")
    return cleaned


class SupabaseStore:
    def __init__(self, client: Client | None = None) -> None:
        load_dotenv()
        if client is not None:
            self.client = client
            return
        url = _normalize_supabase_url(os.environ.get("SUPABASE_URL") or "")
        key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        self.client = create_client(url, key)

    def ping(self) -> bool:
        self.client.table("simulations").select("id").limit(1).execute()
        return True

    def wipe_all_simulations(self) -> int:
        data = self.client.table("simulations").select("id").execute().data or []
        if not data:
            return 0
        self.client.table("simulations").delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()
        return len(data)

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
        payload = {
            "id": sim_id,
            "name": name,
            "season": season,
            "mode": mode,
            "config_name": config_name,
            "mlflow_run_id": mlflow_run_id,
            "status": "in_progress",
            "current_gw": current_gw,
            "total_points": 0,
        }
        sim = self.client.table("simulations").insert(payload).execute().data[0]
        chips = []
        for ent in chip_entitlements:
            row = {
                "id": str(uuid4()),
                "simulation_id": sim_id,
                "chip_type": ent["chip_type"],
                "entitlement": ent["entitlement"],
                "available_from_gw": ent["available_from_gw"],
                "expires_after_gw": ent["expires_after_gw"],
            }
            chips.append(row)
        if chips:
            self.client.table("simulation_chips").insert(chips).execute()
        sim["chips"] = self.list_chips(sim_id)
        return sim

    def get_simulation(self, simulation_id: str) -> dict[str, Any] | None:
        data = (
            self.client.table("simulations")
            .select("*")
            .eq("id", simulation_id)
            .limit(1)
            .execute()
            .data
        )
        return data[0] if data else None

    def update_simulation(self, simulation_id: str, **fields: Any) -> dict[str, Any]:
        data = (
            self.client.table("simulations")
            .update(fields)
            .eq("id", simulation_id)
            .execute()
            .data
        )
        return data[0]

    def list_chips(self, simulation_id: str) -> list[dict[str, Any]]:
        return (
            self.client.table("simulation_chips")
            .select("*")
            .eq("simulation_id", simulation_id)
            .execute()
            .data
        )

    def mark_chip_used(self, chip_id: str, used_gw: int) -> dict[str, Any]:
        return (
            self.client.table("simulation_chips")
            .update({"used_gw": used_gw})
            .eq("id", chip_id)
            .execute()
            .data[0]
        )

    def upsert_gameweek(self, simulation_id: str, gw: int, **fields: Any) -> dict[str, Any]:
        existing = self.get_gameweek(simulation_id, gw)
        if existing:
            data = (
                self.client.table("manager_gameweeks")
                .update(fields)
                .eq("id", existing["id"])
                .execute()
                .data
            )
            return data[0]
        payload = {"id": str(uuid4()), "simulation_id": simulation_id, "gw": gw, **fields}
        return self.client.table("manager_gameweeks").insert(payload).execute().data[0]

    def get_gameweek(self, simulation_id: str, gw: int) -> dict[str, Any] | None:
        data = (
            self.client.table("manager_gameweeks")
            .select("*")
            .eq("simulation_id", simulation_id)
            .eq("gw", gw)
            .limit(1)
            .execute()
            .data
        )
        return data[0] if data else None

    def get_gameweek_by_id(self, manager_gameweek_id: str) -> dict[str, Any] | None:
        data = (
            self.client.table("manager_gameweeks")
            .select("*")
            .eq("id", manager_gameweek_id)
            .limit(1)
            .execute()
            .data
        )
        return data[0] if data else None

    def replace_squad(self, manager_gameweek_id: str, players: list[dict[str, Any]]) -> None:
        self.client.table("squad_players").delete().eq(
            "manager_gameweek_id", manager_gameweek_id
        ).execute()
        rows = []
        for player in players:
            rows.append({"id": str(uuid4()), "manager_gameweek_id": manager_gameweek_id, **player})
        if rows:
            self.client.table("squad_players").insert(rows).execute()

    def list_squad(self, manager_gameweek_id: str) -> list[dict[str, Any]]:
        return (
            self.client.table("squad_players")
            .select("*")
            .eq("manager_gameweek_id", manager_gameweek_id)
            .execute()
            .data
        )

    def add_transfers(
        self, manager_gameweek_id: str, transfers: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        rows = []
        for move in transfers:
            rows.append({"id": str(uuid4()), "manager_gameweek_id": manager_gameweek_id, **move})
        if rows:
            self.client.table("transfers").insert(rows).execute()
        return rows

    def list_transfers(self, manager_gameweek_id: str) -> list[dict[str, Any]]:
        return (
            self.client.table("transfers")
            .select("*")
            .eq("manager_gameweek_id", manager_gameweek_id)
            .execute()
            .data
        )

    def replace_player_points(
        self, manager_gameweek_id: str, rows: list[dict[str, Any]]
    ) -> None:
        self.client.table("player_points").delete().eq(
            "manager_gameweek_id", manager_gameweek_id
        ).execute()
        payload = [
            {"id": str(uuid4()), "manager_gameweek_id": manager_gameweek_id, **row} for row in rows
        ]
        if payload:
            self.client.table("player_points").insert(payload).execute()

    def list_player_points(self, manager_gameweek_id: str) -> list[dict[str, Any]]:
        return (
            self.client.table("player_points")
            .select("*")
            .eq("manager_gameweek_id", manager_gameweek_id)
            .execute()
            .data
        )
