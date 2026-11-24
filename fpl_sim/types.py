from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

Position = Literal["GK", "DEF", "MID", "FWD"]
Phase = Literal["pre_deadline", "post_gameweek"]
ChipType = Literal["wildcard", "freehit", "bboost", "3xc"]

ELEMENT_TYPE_TO_POSITION: dict[int, Position] = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


def tenths_to_millions(tenths: int | float | None) -> float | None:
    if tenths is None:
        return None
    return round(int(tenths) / 10.0, 1)


def millions_to_tenths(millions: int | float) -> int:
    return int(round(float(millions) * 10))


class PlayerView(BaseModel):
    player_id: int
    web_name: str
    first_name: str | None = None
    second_name: str | None = None
    team_id: int
    team_name: str
    position: Position
    element_type: int
    now_cost: int
    price: float
    status: str | None = None
    news: str | None = None
    chance_of_playing_this_round: float | None = None
    chance_of_playing_next_round: float | None = None
    can_select: bool = True
    can_transact: bool = True
    removed: bool = False
    selected_by_percent: float | None = None
    form: float | None = None
    total_points: int | None = None
    event_points: int | None = None
    minutes: int | None = None
    starts: int | None = None
    points_per_game: float | None = None
    ep_this: float | None = None
    ep_next: float | None = None
    goals_scored: int | None = None
    assists: int | None = None
    clean_sheets: int | None = None
    bonus: int | None = None
    goals_conceded: int | None = None
    defensive_contribution: int | None = None
    tackles: int | None = None
    clearances_blocks_interceptions: int | None = None
    expected_goals: float | None = None
    expected_assists: float | None = None
    expected_goal_involvements: float | None = None
    saves: int | None = None
    penalties_saved: int | None = None
    ict_index: float | None = None
    yellow_cards: int | None = None
    red_cards: int | None = None
    transfers_in_event: int | None = None
    transfers_out_event: int | None = None
    history_2024_25: dict[str, Any] | None = None
    history_2023_24: dict[str, Any] | None = None


class SquadMember(BaseModel):
    player_id: int
    purchase_price_tenths: int
    selling_price_tenths: int
    is_starter: bool = False
    bench_order: int | None = None
    is_captain: bool = False
    is_vice_captain: bool = False
    is_reserve_gk: bool = False


class TransferMove(BaseModel):
    player_out_id: int
    player_in_id: int
    sell_price_tenths: int | None = None
    buy_price_tenths: int | None = None


class PendingDecision(BaseModel):
    player_ids: list[int] | None = None
    members: list[SquadMember] | None = None
    starters: list[int] | None = None
    bench_outfield: list[int] | None = None
    reserve_gk: int | None = None
    captain_id: int | None = None
    vice_captain_id: int | None = None
    chip_type: ChipType | None = None
    transfers: list[TransferMove] = Field(default_factory=list)
    summary: str | None = None
    free_hit_base_player_ids: list[int] | None = None


class ValidationResult(BaseModel):
    accepted: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(cls, **data: Any) -> ValidationResult:
        return cls(accepted=True, data=data)

    @classmethod
    def fail(cls, *errors: str, **data: Any) -> ValidationResult:
        return cls(accepted=False, errors=[e for e in errors if e], data=data)


@dataclass
class SessionStats:
    tool_calls: int = 0
    invalid_actions: int = 0
    tool_errors: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    turns: int = 0
    extra: dict[str, Any] = field(default_factory=dict)
