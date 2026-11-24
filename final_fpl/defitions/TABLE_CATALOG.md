# Table catalog

| Location / file pattern | One row represents | Timing and use |
| --- | --- | --- |
| `pre_gw01_player_profiles.csv` | One selectable player at the GW1 deadline | Starting player universe, status, price, and up to two prior-season profiles |
| `gw_player_profile/pre_gwNN_player_stats.csv` | One player available in FPL immediately before GW `NN` | The full live player profile visible to a manager before that deadline |
| `gw_fixtures_snapshots/pre_gwNN.csv` | One of the season's 380 fixtures not yet played | Remaining schedule as known before GW `NN`; supports blanks, doubles, and unassigned postponed fixtures |
| `gw_results_details/results_through_gwNN.csv` | One completed fixture through GW `NN` | Cumulative results view; current GW's fixtures are listed first, in fixture-snapshot order |
| `gw_player_performances/gwNN_player_performance.csv` | One player available in FPL at that Gameweek | Player's aggregate FPL performance across all fixtures in GW `NN`; zeros are retained for blanks/non-appearances |
| `gw_player_fixture_stats/gwNN_player_fixture_stats.csv` | One player–fixture combination in GW `NN` | Normalised FPL `explain` data. A player in a double GW may have two rows; blank-team players have none |
| `gw_awards/gameweek_awards.csv` | One Gameweek | FPL community/captaincy leaders known from the associated event and pre-deadline snapshot |
| `gw_awards/chip_usage.csv` | One Gameweek–chip pair | Number of FPL managers who played that chip in the Gameweek |
| `gw_awards/totw/gw_NN_team_of_the_week.csv` | One Team-of-the-Week player | FPL's 11-player Dream Team for that Gameweek |
| `gw_awards/gameweek_totw.csv` | One Team-of-the-Week player | Combined chronological FPL Dream Team records for all 38 Gameweeks |
| `gw_standings/pre_gwNN_standings.csv` | One Premier League team | Standings immediately before GW `NN`; only matches completed by then count |
| `historical_match_results/past_3_seasons_results.csv` | One fixture from 2022/23–2024/25 | Historical result/event reference, with IDs reconciled to 2025/26 when possible |

## Join guidance

- Use `fixture_id` for 2025/26 fixture/result/per-fixture joins.
- Use `(gameweek, player_id)` for most Gameweek player-table joins.
- Use `(gameweek, fixture_id, player_id)` for the per-fixture player table.
- Use `team_id` only within 2025/26 tables. In historical results use the explicitly named `*_2025_26_id` fields and accept blanks for clubs absent in 2025/26.
- `player_name` and `team_name` are readable labels, not stable keys.

## Time-travel rule

For a decision before GW `NN`, use the matching `pre_gwNN` fixtures, player profiles, and standings. Do not use a later snapshot to infer a future rescheduling, price/status change, transfer trend, or performance outcome.
