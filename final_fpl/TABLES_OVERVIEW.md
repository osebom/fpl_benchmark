# `final_fpl` table overview

This folder is a time-aware 2025/26 FPL simulation dataset. For any decision before Gameweek `NN`, use the matching pre-deadline (`pre_gwNN`) files so the model cannot see later results, transfers, availability changes, or fixture rescheduling.

| Location / table pattern | What it contains | Row grain | Best use |
| --- | --- | --- | --- |
| `pre_gw01_player_profiles.csv` | All players available at the GW1 deadline, their FPL profile, price, availability, and up to two prior-season profiles | One player | Initialise the simulation's selectable player pool and starting values |
| `gw_player_profile/pre_gwNN_player_stats.csv` | Full FPL player profiles immediately before each GW2–GW38 deadline | One available player | Player price, team, fitness/status, ownership, form, cumulative FPL statistics, and transfer information at decision time |
| `gw_player_profile/snapshot_manifest.csv` | Inventory of the pre-deadline player-profile files | One Gameweek | Check snapshot/deadline coverage and player-row counts |
| `gw_fixtures_snapshots/pre_gwNN.csv` | All remaining fixtures as publicly known before each Gameweek | One unplayed fixture | Upcoming schedule, FDR, blank Gameweeks, double Gameweeks, and known postponements without future leakage |
| `gw_results_details/results_through_gwNN.csv` | Results completed through each Gameweek; newest Gameweek appears first | One completed fixture | Give the simulator the match results it should know after each GW |
| `gw_player_performances/gwNN_player_performance.csv` | Aggregate player FPL performance across each Gameweek's fixture(s) | One player in one Gameweek | Quickly show who performed well, including blank and double Gameweeks |
| `gw_player_performances/snapshot_manifest.csv` | Inventory of aggregate player-performance files | One Gameweek | Validate Gameweek file availability and row counts |
| `gw_player_fixture_stats/gwNN_player_fixture_stats.csv` | Normalised FPL `explain`/scoring detail for each player in each fixture | One player–fixture pair | Match-level FPL points, goals, assists, cards, saves, bonus, defensive contribution, and points adjustments; a player can have two rows in a double GW |
| `gw_player_fixture_stats/snapshot_manifest.csv` | Inventory of per-fixture player-stat files | One Gameweek | Check per-fixture row counts and players who appeared |
| `gw_awards/gameweek_awards.csv` | Most-transferred in/out, most-captained, and most-vice-captained players for each Gameweek | One Gameweek | Represent FPL manager sentiment and captaincy trends |
| `gw_awards/chip_usage.csv` | Aggregate FPL chip usage | One Gameweek–chip combination | Model how widely each chip was used in a Gameweek |
| `gw_awards/totw/gw_NN_team_of_the_week.csv` | FPL Team of the Week/Dream Team for an individual Gameweek | One selected player | Per-GW 11-player award view |
| `gw_awards/gameweek_totw.csv` | All FPL Teams of the Week/Dream Teams combined | One selected player | Chronological all-Gameweek Team of the Week analysis |
| `gw_standings/pre_gwNN_standings.csv` | Premier League standings immediately before each GW2–GW38 deadline | One club | Current league position, record, goals, and points; naturally reflects blanks, doubles, and games in hand |
| `historical_match_results/past_3_seasons_results.csv` | Premier League results from 2022/23 to 2024/25, with goals, assists, and own goals | One historical fixture | Historical context; maps players/teams to 2025/26 IDs where possible, otherwise leaves their ID null |

## Important conventions

- `fixture_id`, `player_id`, and `team_id` are FPL IDs. Player/team IDs can change between seasons, so do not join historical IDs directly without using the explicit `*_2025_26_id` fields.
- `*_id_array` fields are JSON arrays. Repeated IDs preserve repeated goals or assists.
- Empty `assigned_gw` in a fixture snapshot means the fixture was known to be postponed but no new Gameweek was public yet.
- `team_h_difficulty` and `team_a_difficulty` are the chosen static FPL Fixture Difficulty Ratings, from 1 (easiest) to 5 (hardest).
- `fpl_3_bonus_player_*` identifies players awarded three FPL bonus points. It is not an official Premier League Man of the Match field.

For field-by-field definitions, see the detailed documentation in [`defitions/`](defitions/README.md).
