# Gameweek performances and awards

## `gw_player_performances/gwNN_player_performance.csv`

One row is one player available to FPL in Gameweek `NN`. All statistic fields below are the player's **aggregate across their fixtures in that Gameweek**, not cumulative season totals.

| Field | Definition |
| --- | --- |
| `gameweek` | Completed Gameweek. |
| `data_available_snapshot_utc` | Cache/snapshot timestamp used for the player universe and labels. |
| `player_id`, `player_name`, `team_id`, `team_name`, `position_name` | Player and team identity at that time, plus FPL position. |
| `team_fixtures_in_gameweek` | Number of fixtures the player's team had in this GW: 0 blank, 1 normal, 2 double. |
| `player_fixture_count` | Number of FPL fixture records attributed to the player. |
| `player_fixture_ids` | JSON array of relevant FPL fixture IDs. |
| `minutes`, `starts`, `goals_scored`, `assists`, `clean_sheets`, `goals_conceded`, `own_goals`, `penalties_saved`, `penalties_missed`, `yellow_cards`, `red_cards`, `saves` | Aggregate individual match statistics; meanings are as in [PLAYER_FIELDS.md](PLAYER_FIELDS.md). |
| `bonus`, `bps`, `influence`, `creativity`, `threat`, `ict_index` | Aggregate FPL bonus, BPS, and ICT statistics in that GW. |
| `clearances_blocks_interceptions`, `recoveries`, `tackles`, `defensive_contribution` | Aggregate defensive-action metrics. |
| `expected_goals`, `expected_assists`, `expected_goal_involvements`, `expected_goals_conceded` | Aggregate FPL expected statistics. |
| `total_points` | Total FPL points earned over all the player's fixtures in that GW. |
| `in_dreamteam` | Whether FPL marked the player as being in that GW's Dream Team. |
| `fixture_points_breakdown` | JSON array of FPL's per-fixture `explain` point records; use the normalised per-fixture table for easier analysis. |

## `gw_player_fixture_stats/gwNN_player_fixture_stats.csv`

One row is a player–fixture record normalised from FPL's `explain` data. This table provides the match-level detail behind the aggregate performance table.

| Field | Definition |
| --- | --- |
| `gameweek`, `data_available_snapshot_utc` | Completed Gameweek and relevant cached timestamp. |
| `fixture_id`, `kickoff_time` | FPL fixture ID and kickoff timestamp. |
| `home_team_id`, `home_team_name`, `home_score`, `away_team_id`, `away_team_name`, `away_score` | Fixture participants and final score. |
| `player_id`, `player_name`, `player_team_id`, `player_team_name`, `position_name` | Player identity, club at the time, and FPL position. |
| `venue` | `home` or `away` from the player's viewpoint. |
| `opponent_team_id`, `opponent_team_name` | Opposing club. |
| `did_play` | True when the player recorded minutes in this fixture. A row may exist with false because the FPL explain data lists the player but they did not appear. |
| `fixture_fpl_points` | Total FPL points allocated to the player for this fixture. |
| `assists`, `bonus`, `clean_sheets`, `defensive_contribution`, `goals_conceded`, `goals_scored`, `minutes`, `own_goals`, `penalties_missed`, `penalties_saved`, `red_cards`, `saves`, `yellow_cards` | Match statistic count/value for that named FPL scoring category. |
| `<stat>_fpl_points` | FPL points credited for that named statistic/category in this fixture. |
| `<stat>_points_modification` | Separate adjustment attached by FPL to that category, e.g. a points modification/adjustment in the `explain` payload. |

`fixture_fpl_points` is the sum of the category point and modification values. It is FPL scoring attribution, not a Premier League event-feed reconstruction.

## Awards and chip usage

### `gw_awards/gameweek_awards.csv`

| Field | Definition |
| --- | --- |
| `gameweek`, `deadline_utc`, `source_snapshot_utc` | Upcoming GW, its deadline, and source snapshot time. |
| `average_manager_score` | FPL's published `average_entry_score`: average points scored by ranked FPL manager entries in that Gameweek. |
| `highest_manager_score` | FPL's published `highest_score`: highest points total achieved by an FPL manager entry in that Gameweek. |
| `player_of_gameweek_id`, `player_of_gameweek_name`, `player_of_gameweek_team_id`, `player_of_gameweek_team_name`, `player_of_gameweek_points` | FPL's `top_element` footballer for the Gameweek, their club at the deadline snapshot, and FPL's `top_element_info.points` score. This is the highest-scoring footballer in FPL terms, not an official Premier League award. |
| `most_transferred_in_id`, `most_transferred_in_name`, `most_transferred_in_team_id`, `most_transferred_in_team_name` | Player FPL identified as the event's most transferred-in player and their club. The API provides an identity, not a corresponding count in this table. |
| `most_transferred_out_id`, `most_transferred_out_name`, `most_transferred_out_team_id`, `most_transferred_out_team_name` | Player with the highest `transfers_out_event` in the relevant pre-deadline snapshot and their club. |
| `most_transferred_out_count` | That player's event-level transfer-out count. |
| `most_captained_id`, `most_captained_name`, `most_captained_team_id`, `most_captained_team_name` | Event's most-captained player and club. |
| `most_vice_captained_id`, `most_vice_captained_name`, `most_vice_captained_team_id`, `most_vice_captained_team_name` | Event's most vice-captained player and club. |

### `gw_awards/chip_usage.csv`

| Field | Definition |
| --- | --- |
| `gameweek` | Gameweek in which a chip was played. |
| `chip_name` | FPL chip identifier/name. |
| `number_played` | Number of managers recorded by FPL as using that chip in the Gameweek. |

### `gw_awards/totw/gw_NN_team_of_the_week.csv` and `gw_awards/gameweek_totw.csv`

| Field | Definition |
| --- | --- |
| `gameweek` | Gameweek of the FPL Team of the Week / Dream Team selection. |
| `player_id`, `player_name`, `team_id`, `team_name`, `position` | Selected player's FPL identity, club and position label. |
| `total_points`, `minutes`, `goals_scored`, `assists`, `clean_sheets`, `saves`, `bonus`, `bps` | That player's Gameweek values for the listed FPL statistics. |

The `totw` folder stores one 11-player file per Gameweek. `gameweek_totw.csv` combines all 38 Gameweeks into one chronological table.
