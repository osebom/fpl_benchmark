# Standings and manifest fields

## `gw_standings/pre_gwNN_standings.csv`

One row is one club's league-table position immediately before the GW `NN` deadline. It includes all completed matches by that time, so double and postponed fixtures are inherently reflected.

| Field | Definition |
| --- | --- |
| `gameweek` | Upcoming Gameweek for which the pre-deadline table was prepared. |
| `standings_as_of_utc` | Timestamp through which results were included. |
| `position` | Calculated league-table position in this dataset. |
| `team_id`, `team_name` | 2025/26 FPL team ID and display name. |
| `played`, `wins`, `draws`, `losses` | Completed league-match record. |
| `goals_for`, `goals_against`, `goal_difference` | Goals scored, conceded, and their difference. |
| `points` | League points (three for a win, one for a draw). |

## `snapshot_manifest.csv` files

Manifests are inventories rather than player or fixture records.

### `gw_player_profile/snapshot_manifest.csv`

| Field | Definition |
| --- | --- |
| `gameweek` | Upcoming Gameweek represented by the profile file. |
| `file_name` | Filename of that snapshot. |
| `deadline_utc` | FPL deadline for that Gameweek. |
| `snapshot_utc` | Latest available cache timestamp before the deadline. |
| `player_rows` | Number of available player rows in the file. |
| `stat_columns` | Number of raw FPL player-stat columns included. |

### `gw_player_performances/snapshot_manifest.csv`

| Field | Definition |
| --- | --- |
| `gameweek` | Completed Gameweek. |
| `file_name` | Filename of its aggregate performance table. |
| `data_available_snapshot_utc` | Snapshot timestamp from which player availability/identity was taken. |
| `players` | Number of player rows in the table. |
| `stat_columns` | Number of performance-stat columns. |

### `gw_player_fixture_stats/snapshot_manifest.csv`

| Field | Definition |
| --- | --- |
| `gameweek` | Completed Gameweek. |
| `file_name` | Filename of its normalised per-fixture player table. |
| `player_fixture_rows` | Number of player–fixture rows, including rows for players who did not play. |
| `players_who_played` | Number of distinct players with `did_play = true`. |
