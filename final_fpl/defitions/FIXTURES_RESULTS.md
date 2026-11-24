# Fixtures and results fields

## `gw_fixtures_snapshots/pre_gwNN.csv`

One row is an unplayed 2025/26 Premier League fixture as it was known before the stated deadline.

| Field | Definition |
| --- | --- |
| `snapshot_gameweek` | Gameweek the manager is about to enter. |
| `snapshot_deadline_utc` | Official FPL deadline used for this snapshot. |
| `fixture_id` | FPL fixture identifier. |
| `home_team_id`, `away_team_id` | 2025/26 FPL IDs of the home and away clubs. |
| `home_team_name`, `away_team_name` | Club display names. |
| `assigned_gw` | Gameweek to which the match had been assigned at that point. Empty/null means it was postponed/unassigned, so its replacement date was not yet public. |
| `fixture_status` | Project status: `scheduled` when assigned, `postponed` when known postponed without a new assignment, or another source status if present. |
| `team_h_difficulty`, `team_a_difficulty` | Static FPL Fixture Difficulty Rating (1 easiest, 5 hardest) for the home/away team respectively. |

The files intentionally omit games already played. A double Gameweek appears naturally when a team has two remaining rows with the same `assigned_gw`; a blank appears when it has none.

## `gw_results_details/results_through_gwNN.csv`

Each file contains results through that Gameweek and presents the newest Gameweek first.

| Field | Definition |
| --- | --- |
| `fixture_id` | 2025/26 FPL fixture ID. |
| `gameweek` | Gameweek in which the fixture was played. |
| `kickoff_time` | Actual/scheduled FPL kickoff timestamp recorded for the fixture. |
| `home_team_id`, `away_team_id` | 2025/26 FPL team IDs. |
| `home_team_name`, `away_team_name` | Team display names. |
| `home_score`, `away_score` | Final goals scored by the home/away team. |
| `home_goalscorer_ids`, `away_goalscorer_ids` | Comma-separated distinct FPL IDs of scorers for that side. |
| `home_goalscorer_names`, `away_goalscorer_names` | Matching comma-separated scorer names. |
| `home_goal_scorer_id_array`, `away_goal_scorer_id_array` | JSON scorer ID sequence, with one entry per goal; repeated IDs preserve braces. |
| `own_goal_scorer_ids`, `own_goal_scorer_names` | Comma-separated distinct players credited with an own goal. |
| `own_goal_scorer_id_array` | JSON own-goal scorer IDs, one entry per own goal. |
| `own_goal_team_ids`, `own_goal_team_names` | Teams for which the own-goal scorers played — the side that conceded the own goal, not the beneficiary. |
| `fpl_3_bonus_player_ids`, `fpl_3_bonus_player_names` | Players who received exactly three FPL bonus points in this fixture. This is an FPL bonus field, **not** an official Premier League Man of the Match. More than one player can receive three points in a tie. |

## `historical_match_results/past_3_seasons_results.csv`

One row is a completed fixture from 2022/23, 2023/24, or 2024/25.

| Field | Definition |
| --- | --- |
| `season` | Season label for the historical fixture. |
| `fixture_id` | FPL fixture ID from that historical season; it is not comparable with 2025/26 fixture IDs. |
| `gameweek`, `kickoff_time`, `home_score`, `away_score` | Historical fixture's played Gameweek, kickoff, and final score. |
| `home_team_2025_26_id`, `away_team_2025_26_id` | 2025/26 FPL ID for the club if that club competed in 2025/26; blank otherwise. |
| `home_team_name`, `away_team_name` | Historical club names. |
| `home_goalscorer_2025_26_id_array`, `away_goalscorer_2025_26_id_array` | JSON scorer sequence mapped to the player's 2025/26 FPL ID where available; `null` entry means that player was unavailable in 2025/26. |
| `home_goalscorer_names`, `away_goalscorer_names` | Names corresponding to the scorer arrays. |
| `home_assister_2025_26_id_array`, `away_assister_2025_26_id_array` | JSON assister sequence using the same 2025/26 mapping/null convention. |
| `home_assister_names`, `away_assister_names` | Names corresponding to assister arrays. |
| `home_own_goal_scorer_2025_26_id_array`, `away_own_goal_scorer_2025_26_id_array` | JSON own-goal scorer arrays, split by the side whose player scored the own goal; mapped/null as above. |
| `home_own_goal_scorer_names`, `away_own_goal_scorer_names` | Names corresponding to own-goal arrays. |
