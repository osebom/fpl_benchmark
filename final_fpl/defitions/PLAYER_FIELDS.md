# Player profile fields

These definitions apply to the raw FPL player fields in `pre_gw01_player_profiles.csv` and every `gw_player_profile/pre_gwNN_player_stats.csv`. Unless stated otherwise, they are cumulative **within the current season at that snapshot**. FPL commonly serialises decimal metrics as text; preserve them as numeric values when analysing.

`pre_gw01_player_profiles.csv` also contains `history_2023_24_*` and `history_2024_25_*` versions of these fields. The suffix after either prefix has the identical definition below, but is the value retained from that historical season. `history_YYYY_YY_available` is true when a usable FPL profile for that player/season exists.

## Snapshot, identity, team and position

| Field | Definition |
| --- | --- |
| `snapshot_timestamp_utc` | Timestamp of the GW1 player snapshot. |
| `gw1_deadline_utc` | Official GW1 deadline. |
| `season` | Season label for the unprefixed profile. |
| `id` | Season-specific FPL element/player ID. |
| `code` | FPL's persistent player code used to identify a real player across many FPL records. |
| `opta_code` | Opta provider player identifier, where supplied. |
| `first_name`, `second_name`, `web_name`, `known_name` | First name, surname, FPL display name, and alternative known name where supplied. |
| `photo` | FPL photo filename/path token. |
| `birth_date` | Date of birth. |
| `region` | FPL region/nationality code, where supplied. |
| `team` | Season-specific FPL team ID. |
| `team_name` | Resolved display name for `team`; added by this project. |
| `team_code` | FPL internal club code. |
| `team_join_date` | Date the player joined their then-current club, where supplied. |
| `squad_number` | Shirt number, if assigned. |
| `element_type` | FPL position code: 1 goalkeeper, 2 defender, 3 midfielder, 4 forward. |
| `position_name` | Resolved FPL position label; added by this project. |

## Availability, news and selection

| Field | Definition |
| --- | --- |
| `status` | FPL availability code: normally `a` available, `d` doubtful, `i` injured, `s` suspended, `u` unavailable, or `n` not in squad. |
| `chance_of_playing_this_round`, `chance_of_playing_next_round` | FPL's stated percentage chance of appearing in the current/next Gameweek. Empty means FPL did not publish a percentage. |
| `news`, `news_added` | Latest FPL news text and the timestamp it was added. |
| `scout_news_link`, `scout_risks` | Optional FPL Scout information/link and risk flags where supplied. |
| `can_select`, `can_transact` | Whether the player could be selected in a squad / transferred in at that snapshot. |
| `removed` | Whether FPL had removed the player from the game. |
| `special` | FPL special-status flag. |
| `has_temporary_code` | Whether FPL marked the player's code as temporary. |

## Price, ownership and transfers

| Field | Definition |
| --- | --- |
| `now_cost` | Current FPL price in tenths of a million pounds: 75 means £7.5m. |
| `price_millions` | `now_cost / 10`; added in the GW1 profile for direct readability. |
| `cost_change_event`, `cost_change_event_fall` | Net price movement / downward movement in the current Gameweek, in 0.1m units. |
| `cost_change_start`, `cost_change_start_fall` | Net price movement / downward movement since the season start, in 0.1m units. |
| `price_change_percent` | Price change as a percentage where supplied by FPL. |
| `now_cost_rank`, `now_cost_rank_type` | Rank by price overall / within FPL position. |
| `selected_by_percent` | Percentage of FPL teams owning the player. |
| `selected_rank`, `selected_rank_type` | Ownership rank overall / within position. |
| `transfers_in`, `transfers_out` | Cumulative transfers in/out during the season. |
| `transfers_in_event`, `transfers_out_event` | Transfers in/out in the current Gameweek. |
| `value_form`, `value_season` | FPL value measures: recent form per price and season points per price. |

## FPL points, appearances and base match outcomes

| Field | Definition |
| --- | --- |
| `total_points` | Cumulative FPL points. |
| `event_points` | FPL points in the current/latest Gameweek. |
| `points_per_game` | Average FPL points per appearance/game as published by FPL. |
| `points_per_game_rank`, `points_per_game_rank_type` | Points-per-game rank overall / within position. |
| `form` | FPL's rolling recent-points form metric. |
| `form_rank`, `form_rank_type` | Form rank overall / within position. |
| `ep_this`, `ep_next` | FPL expected points for the current and next Gameweek. Treat as snapshot-time estimates, not outcomes. |
| `minutes`, `starts`, `starts_per_90` | Minutes played, starts, and starts per 90 minutes. |
| `goals_scored`, `assists`, `own_goals` | Goals, FPL assists, and own goals. |
| `clean_sheets`, `clean_sheets_per_90` | Clean sheets and clean sheets per 90. |
| `goals_conceded`, `goals_conceded_per_90` | Goals conceded while on the pitch and rate per 90. |
| `saves`, `saves_per_90`, `penalties_saved` | Saves, saves per 90, and saved penalties. |
| `penalties_missed` | Missed penalties. |
| `yellow_cards`, `red_cards` | Cards received. |

## BPS, Dream Team, ICT and expected statistics

| Field | Definition |
| --- | --- |
| `bonus` | Cumulative FPL bonus points. |
| `bps` | Cumulative Bonus Points System score (the underlying ranking score, not necessarily FPL points). |
| `in_dreamteam`, `dreamteam_count` | Whether the player is in the current FPL Dream Team and number of Dream Team selections. |
| `influence`, `creativity`, `threat`, `ict_index` | FPL/Opta ICT component scores and their combined ICT Index. |
| `influence_rank`, `creativity_rank`, `threat_rank`, `ict_index_rank` | Overall rank for the named metric. |
| `influence_rank_type`, `creativity_rank_type`, `threat_rank_type`, `ict_index_rank_type` | Rank for the named metric within FPL position. |
| `expected_goals`, `expected_assists`, `expected_goal_involvements`, `expected_goals_conceded` | Cumulative xG, xA, xGI, and xGC supplied by FPL. |
| `expected_goals_per_90`, `expected_assists_per_90`, `expected_goal_involvements_per_90`, `expected_goals_conceded_per_90` | The corresponding expected-stat rates per 90 minutes. |

## Defensive actions and set-piece information

| Field | Definition |
| --- | --- |
| `tackles`, `recoveries` | Tackles and ball recoveries. |
| `clearances_blocks_interceptions` | Combined clearances, blocks, and interceptions. |
| `defensive_contribution`, `defensive_contribution_per_90` | FPL defensive-contribution measure and rate per 90. It is a data metric; any scoring threshold belongs in FPL game rules, not this definition. |
| `penalties_order`, `penalties_text` | Penalty-taking priority and supporting text. |
| `direct_freekicks_order`, `direct_freekicks_text` | Direct free-kick priority and supporting text. |
| `corners_and_indirect_freekicks_order`, `corners_and_indirect_freekicks_text` | Corner/indirect-free-kick priority and supporting text. |

## Manager fields in historical profile data

These only occur under the `history_2024_25_` prefix and describe the FPL manager game introduced in that season:

| Suffix | Definition |
| --- | --- |
| `mng_clean_sheets` | Manager clean-sheet points/stat. |
| `mng_draw` | Manager draw points/stat. |
| `mng_goals_scored` | Manager goals-scored points/stat. |
| `mng_loss` | Manager loss points/stat. |
| `mng_underdog_draw`, `mng_underdog_win` | Manager underdog draw/win points/stat. |
| `mng_win` | Manager win points/stat. |
