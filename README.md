# FPL Agent Simulation

Time-aware Fantasy Premier League harness for the 2025/26 season. An LLM manages one team Gameweek by Gameweek and can only see information that was public at each historical deadline.

Strategy is model-driven. Rules, scoring, historical information boundaries, and state transitions are deterministic.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Fill `.env`:

- `COHERE_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- Databricks MLflow (see below)

In the Supabase SQL editor, run [`storage/migrations/001_init.sql`](storage/migrations/001_init.sql). If you already applied an older `001`, run [`storage/migrations/002_lock_on_lineup.sql`](storage/migrations/002_lock_on_lineup.sql) (wipes leftover simulation rows, flattens transfers, drops `decisions`).

## Databricks MLflow tracing

Hosted MLflow lives in your Databricks workspace. Traces from each Gameweek agent session (LLM turns + tool calls) show up on the experiment **Traces** tab.

1. Open Databricks → **Experiments** → **GenAI apps & agents** (or create an experiment).
2. Open the experiment → kebab menu → **Log traces locally** → **Generate API Key**.
3. Paste the generated values into `.env`:

```
DATABRICKS_HOST=https://<your-workspace>.cloud.databricks.com
DATABRICKS_TOKEN=<personal-access-token>
MLFLOW_TRACKING_URI=databricks
MLFLOW_REGISTRY_URI=databricks-uc
MLFLOW_EXPERIMENT_ID=<experiment-id>
```

If you skip `MLFLOW_EXPERIMENT_ID`, the harness creates/uses `/Shared/fpl_sim` (or `tracking.experiment_name` in [`configs/baseline.yaml`](configs/baseline.yaml)).

Then open [`notebooks/01_historical_simulation.ipynb`](notebooks/01_historical_simulation.ipynb) and run cells in order:

1. `sim.select_initial_team()` — pick GW1 squad and lock on `submit_lineup`
2. `sim.resolve_current()` — score GW1
3. `sim.advance()` — resolve the locked GW and lock the next one

## Layout

| Path | Role |
| --- | --- |
| `final_fpl/` | Immutable 2025/26 world CSVs |
| `fpl_sim/world/` | Time-bounded world repository |
| `fpl_sim/simulator/` | Rules, autosubs, scoring, state transitions |
| `fpl_sim/tools/` | LLM-facing Python tools |
| `fpl_sim/harness/` | Gameweek loop |
| `fpl_sim/storage/` | Supabase manager timeline |
| `configs/` | Experiment + rules YAML |
| `skills/` | Manager Skill (process, not rules) |

## Tests

```bash
pytest
```

## MCP

The notebook calls Python tools directly. An optional FastMCP wrapper is available:

```bash
fpl-mcp
```
