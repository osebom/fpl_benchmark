from __future__ import annotations

from pathlib import Path

from fpl_sim.paths import repo_root
from fpl_sim.types import tenths_to_millions
from fpl_sim.world.repository import FPLWorldRepository


SYSTEM_PREFIX = """You are an FPL manager in a historical simulation.
You cannot control the Gameweek clock. Tools only return information that was public at this deadline.
Propose actions through tools. Invalid actions are rejected and not saved. Correct them and continue.
GW1: submit_initial_squad, then submit_lineup. GW2+: optional submit_transfers, then submit_lineup.
An accepted submit_lineup locks the Gameweek.
"""


def load_skill(path: str | Path | None) -> str:
    if not path:
        return ""
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = repo_root() / resolved
    return resolved.read_text()


def build_system_prompt(skill_text: str) -> str:
    parts = [SYSTEM_PREFIX.strip()]
    if skill_text:
        parts.append(skill_text.strip())
    return "\n\n".join(parts)


def format_squad_line(repo: FPLWorldRepository, player_ids: list[int]) -> str:
    players = repo.current_player_map()
    bits = []
    for pid in player_ids:
        player = players.get(int(pid))
        if not player:
            bits.append(str(pid))
            continue
        bits.append(f"{player.web_name} ({player.position}, {player.team_name}, £{player.price:.1f}m)")
    return "; ".join(bits)


def build_gameweek_brief(
    repo: FPLWorldRepository,
    *,
    gw1: bool,
    bank_tenths: int,
    free_transfers: int | None,
    total_points: int,
    squad_ids: list[int] | None,
    previous: dict | None,
) -> str:
    gw = repo.current_gw
    lines = [f"GAMEWEEK {gw}", ""]
    if previous:
        lines.extend(
            [
                "Previous GW:",
                f"Score: {previous.get('net_points')}",
                f"FPL average: {previous.get('fpl_average')}",
                f"Highest: {previous.get('fpl_highest')}",
                f"Season total: {total_points}",
                f"Previous captain: {previous.get('captain_name')}",
                f"Captain contribution: {previous.get('captain_contribution')}",
                f"Bench points: {previous.get('bench_points')}",
                f"Transfer hit: {previous.get('transfer_hit')}",
                "",
            ]
        )
    elif gw1:
        lines.extend(
            [
                "This is Gameweek 1. Call submit_initial_squad with 15 player_ids, then submit_lineup to lock.",
                "Budget is £100.0m. Transfers are not available. An accepted submit_lineup locks the Gameweek.",
                "2025/26 points have not started. Rank last season with search_players(season='2024_25', sort_by=...).",
                "DEF/MID: points + minutes + defensive_contribution. FWD: points + goals/xG, not DC. GK: saves and clean sheets.",
                "",
            ]
        )
    lines.extend(
        [
            "Manager state:",
            f"Bank: £{tenths_to_millions(bank_tenths) or 0:.1f}m",
            f"Free transfers: {free_transfers}",
        ]
    )
    if squad_ids:
        lines.append(f"Current squad: {format_squad_line(repo, squad_ids)}")
    lines.extend(
        [
            "",
            f"Make your GW{gw} decisions.",
            "Use the available tools to investigate the current world.",
            "Lock by calling submit_lineup once the squad and lineup are valid.",
            "Do not assume last week was a bad decision just because of variance.",
        ]
    )
    return "\n".join(lines)
