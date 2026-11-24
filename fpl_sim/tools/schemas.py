from __future__ import annotations

from typing import Any, Callable

from fpl_sim.tools.context import ToolContext

CORE_V1 = [
    "search_players",
    "get_player",
    "compare_players",
    "get_player_performance",
    "get_team_fixtures",
    "get_standings",
    "get_historical_results",
    "get_manager_state",
    "submit_initial_squad",
    "submit_transfers",
    "submit_lineup",
    "play_chip",
]

EXTENDED = CORE_V1 + [
    "get_player_fixture_history",
    "get_team_results",
    "get_top_performers",
]

SCHEMAS: dict[str, dict[str, Any]] = {
    "search_players": {
        "description": (
            "Search the current pre-deadline player pool and rank a shortlist. "
            "Use sort_by to rank on a stat (total_points, defensive_contribution, "
            "expected_goals, minutes, ...). season=current is this snapshot; "
            "season=2024_25 is last season. At GW1, current counting stats are last year's."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "position": {"type": "string", "enum": ["GK", "DEF", "MID", "FWD"]},
                "team_name": {"type": "string"},
                "team_id": {"type": "integer"},
                "max_price": {"type": "number"},
                "min_price": {"type": "number"},
                "status": {"type": "string"},
                "sort_by": {
                    "type": "string",
                    "enum": [
                        "total_points",
                        "minutes",
                        "starts",
                        "goals_scored",
                        "assists",
                        "clean_sheets",
                        "defensive_contribution",
                        "tackles",
                        "clearances_blocks_interceptions",
                        "expected_goals",
                        "expected_assists",
                        "saves",
                        "bonus",
                        "form",
                        "selected_by_percent",
                        "ict_index",
                        "price",
                    ],
                    "description": (
                        "Stat to rank by (high to low, except price). "
                        "Always consider total_points alongside the specialist stat."
                    ),
                },
                "season": {
                    "type": "string",
                    "enum": ["current", "2024_25", "2023_24", "prior"],
                    "description": "Which season the sort_by / min_minutes values come from.",
                },
                "min_minutes": {
                    "type": "number",
                    "description": "Drop players below this minutes total in the chosen season.",
                },
                "limit": {"type": "integer"},
            },
        },
    },
    "get_player": {
        "description": "Full current-deadline profile for one player, including 2023/24 and 2024/25 highlights when present (points, minutes, goals, xG, DC, saves).",
        "parameters": {
            "type": "object",
            "properties": {"player_id": {"type": "integer"}},
            "required": ["player_id"],
        },
    },
    "compare_players": {
        "description": (
            "Side-by-side compact comparison of up to six players, including last-season highlights when present."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "player_ids": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["player_ids"],
        },
    },
    "get_player_performance": {
        "description": "Completed-Gameweek FPL points for a player. Truncated so future Gameweeks are never returned.",
        "parameters": {
            "type": "object",
            "properties": {
                "player_id": {"type": "integer"},
                "last_n": {"type": "integer"},
            },
            "required": ["player_id"],
        },
    },
    "get_player_fixture_history": {
        "description": "Per-fixture completed scoring history for a player.",
        "parameters": {
            "type": "object",
            "properties": {
                "player_id": {"type": "integer"},
                "last_n": {"type": "integer"},
            },
            "required": ["player_id"],
        },
    },
    "get_team_fixtures": {
        "description": "Remaining fixtures for a club as known at this deadline, including blanks/doubles/postponements.",
        "parameters": {
            "type": "object",
            "properties": {
                "team_id": {"type": "integer"},
                "next_n": {"type": "integer"},
            },
            "required": ["team_id"],
        },
    },
    "get_team_results": {
        "description": "Completed 2025/26 results for a club up to the latest finished Gameweek.",
        "parameters": {
            "type": "object",
            "properties": {"team_id": {"type": "integer"}},
            "required": ["team_id"],
        },
    },
    "get_standings": {
        "description": "Premier League table known at this deadline. Empty before GW1.",
        "parameters": {"type": "object", "properties": {}},
    },
    "get_historical_results": {
        "description": "Premier League results from 2022/23-2024/25. IDs are mapped to 2025/26 where possible.",
        "parameters": {
            "type": "object",
            "properties": {
                "team_id": {"type": "integer"},
                "season": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
    },
    "get_top_performers": {
        "description": "Highest-scoring players over recently completed Gameweeks only.",
        "parameters": {
            "type": "object",
            "properties": {
                "last_n": {"type": "integer"},
                "position": {"type": "string", "enum": ["GK", "DEF", "MID", "FWD"]},
                "limit": {"type": "integer"},
            },
        },
    },
    "get_manager_state": {
        "description": (
            "Your bank, free transfers, chips available this Gameweek, and current squad. "
            "Owned players include selling_price (what you get if you transfer them out)."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    "submit_initial_squad": {
        "description": (
            "GW1 only: propose the 15-player squad. Draft until an accepted submit_lineup locks the Gameweek."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "player_ids": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["player_ids"],
        },
    },
    "submit_transfers": {
        "description": (
            "GW2+ only: propose one or more out/in swaps. Reports bank and hit. "
            "Draft until an accepted submit_lineup locks the Gameweek. Not allowed in GW1."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "transfers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "player_out_id": {"type": "integer"},
                            "player_in_id": {"type": "integer"},
                        },
                        "required": ["player_out_id", "player_in_id"],
                    },
                }
            },
            "required": ["transfers"],
        },
    },
    "submit_lineup": {
        "description": (
            "Set the starting XI, three outfield bench players in priority order, reserve GK, captain, and vice-captain. "
            "An accepted call locks this Gameweek. GW1: call submit_initial_squad first."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "starters": {"type": "array", "items": {"type": "integer"}},
                "bench_outfield": {"type": "array", "items": {"type": "integer"}},
                "reserve_gk": {"type": "integer"},
                "captain_id": {"type": "integer"},
                "vice_captain_id": {"type": "integer"},
            },
            "required": [
                "starters",
                "bench_outfield",
                "reserve_gk",
                "captain_id",
                "vice_captain_id",
            ],
        },
    },
    "play_chip": {
        "description": "Play one eligible chip this Gameweek: wildcard, freehit, bboost, or 3xc.",
        "parameters": {
            "type": "object",
            "properties": {
                "chip_type": {"type": "string", "enum": ["wildcard", "freehit", "bboost", "3xc"]},
            },
            "required": ["chip_type"],
        },
    },
}


def cohere_tools(names: list[str] | None = None) -> list[dict[str, Any]]:
    selected = names or CORE_V1
    tools = []
    for name in selected:
        spec = SCHEMAS[name]
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": spec["description"],
                    "parameters": spec["parameters"],
                },
            }
        )
    return tools


def dispatch(ctx: ToolContext, name: str, arguments: dict[str, Any]) -> Any:
    if not hasattr(ctx, name):
        ctx.stats.tool_errors += 1
        return {"accepted": False, "errors": [f"Unknown tool: {name}"]}
    fn: Callable[..., Any] = getattr(ctx, name)
    ctx.stats.tool_calls += 1
    try:
        return fn(**(arguments or {}))
    except TypeError as exc:
        ctx.stats.tool_errors += 1
        return {"accepted": False, "errors": [f"Bad arguments for {name}: {exc}"]}
    except Exception as exc:  # noqa: BLE001
        ctx.stats.tool_errors += 1
        return {"accepted": False, "errors": [f"{name} failed: {exc}"]}
