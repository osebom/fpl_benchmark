# `final_fpl` data dictionary

This folder documents the CSVs in `final_fpl`.  It is written for a simulation that must only see information available at the relevant FPL deadline.

## Core conventions

- **Season:** unprefixed player and fixture data is for 2025/26 unless a `season` column says otherwise.
- **Time:** `*_utc` values are ISO-8601 UTC timestamps. A `pre_gwNN` file is the latest captured data before that Gameweek's deadline.
- **IDs:** `player_id`, `team_id`, and `fixture_id` are FPL identifiers. IDs are only safe within their season. The historical-results file deliberately uses 2025/26 IDs where a player/team was present in 2025/26; otherwise the ID is blank/null.
- **Blank values:** an empty CSV cell means unknown, not applicable, or unavailable in the source snapshot. It is not automatically zero.
- **Arrays:** `*_id_array` cells are JSON arrays. Repeated IDs represent repeated events, so `[10,10,3]` means player 10 scored twice and player 3 once. Plain `*_ids`/`*_names` cells are comma-separated display lists.
- **Player profile totals:** raw FPL player fields in a profile are cumulative season values as of that snapshot, unless their names explicitly say otherwise. Gameweek-performance files instead contain values for that Gameweek only.
- **FDR:** `team_h_difficulty` and `team_a_difficulty` are the selected static 1–5 FPL difficulty ratings, from the approved 2025/26 fixture source. They are not a model-generated difficulty score and do not change by snapshot.

## Documentation map

| File | Covers |
| --- | --- |
| [TABLE_CATALOG.md](TABLE_CATALOG.md) | Every table/folder, its row grain, timing, and keys |
| [PLAYER_FIELDS.md](PLAYER_FIELDS.md) | All raw player-profile fields, including `history_2023_24_*` and `history_2024_25_*` |
| [FIXTURES_RESULTS.md](FIXTURES_RESULTS.md) | Fixture snapshots, final results, rolling results, and historical results |
| [PERFORMANCES_AWARDS.md](PERFORMANCES_AWARDS.md) | Gameweek player totals, per-fixture player rows, awards, chips, and Team of the Week |
| [STANDINGS_MANIFESTS.md](STANDINGS_MANIFESTS.md) | League tables and all manifest fields |

## Source references

The source data is derived from FPL API snapshots. These references were used to interpret the API fields:

- [FPL Assist Postman API collection](https://www.postman.com/fplassist/fpl-assist/collection/zqlmv01/fantasy-premier-league-api)
- [Microsoft Fantasy Premier League connector reference](https://learn.microsoft.com/en-us/connectors/fantasypremierleagueip/)
- [vaastav Fantasy Premier League data dictionary](https://github.com/vaastav/Fantasy-Premier-League/blob/master/DATA_DICTIONARY.md)

Where the API does not publish a definition, this dictionary says how the field was constructed in this project.
