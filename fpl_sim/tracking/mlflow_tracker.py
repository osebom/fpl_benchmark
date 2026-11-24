from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import mlflow
import yaml
from dotenv import load_dotenv

from fpl_sim.paths import repo_root

_TRACING_ENABLED = False


def tracing_enabled() -> bool:
    return _TRACING_ENABLED


def set_tracing_enabled(enabled: bool) -> None:
    global _TRACING_ENABLED
    _TRACING_ENABLED = enabled


def resolve_tracking_uri() -> str:
    load_dotenv()
    explicit = os.environ.get("MLFLOW_TRACKING_URI")
    if explicit:
        return explicit
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    if host and token:
        return "databricks"
    return f"sqlite:///{repo_root() / 'mlflow.db'}"


def is_databricks_uri(uri: str) -> bool:
    return uri == "databricks" or uri.startswith("databricks://")


def resolve_experiment(config: dict[str, Any], uri: str) -> tuple[str | None, str | None]:
    """Return (experiment_id, experiment_name). ID wins when both are set."""
    exp_id = os.environ.get("MLFLOW_EXPERIMENT_ID") or None
    exp_name = os.environ.get("MLFLOW_EXPERIMENT_NAME") or None
    if exp_id or exp_name:
        return exp_id, exp_name
    configured = (
        config.get("tracking", {}).get("experiment_name")
        or config.get("experiment", {}).get("name")
        or "fpl_sim"
    )
    if is_databricks_uri(uri) and not str(configured).startswith("/"):
        configured = f"/Shared/{configured}"
    return None, str(configured)


class MLflowTracker:
    def __init__(self) -> None:
        load_dotenv()
        self.run_id: str | None = None
        self.enabled = False
        self.tracking_uri: str | None = None
        self.experiment_name: str | None = None
        self.experiment_id: str | None = None

    def start(self, config: dict[str, Any], extra_params: dict[str, Any] | None = None) -> str:
        self.enabled = True
        set_tracing_enabled(True)
        uri = resolve_tracking_uri()
        self.tracking_uri = uri
        mlflow.set_tracking_uri(uri)
        if os.environ.get("MLFLOW_REGISTRY_URI"):
            mlflow.set_registry_uri(os.environ["MLFLOW_REGISTRY_URI"])

        exp_id, exp_name = resolve_experiment(config, uri)
        self.experiment_id = exp_id
        self.experiment_name = exp_name
        if exp_id:
            experiment = mlflow.set_experiment(experiment_id=exp_id)
        else:
            experiment = mlflow.set_experiment(exp_name)
        self.experiment_id = experiment.experiment_id
        self.experiment_name = experiment.name

        run_name = config.get("experiment", {}).get("name", "fpl_sim")
        run = mlflow.start_run(run_name=run_name)
        self.run_id = run.info.run_id
        model = config.get("model", {})
        params = {
            "model": model.get("name"),
            "temperature": model.get("temperature"),
            "seed": model.get("seed"),
            "tool_set": config.get("tools", {}).get("set"),
            "skill_version": config.get("skill", {}).get("version"),
            "memory_type": config.get("memory", {}).get("type"),
            "reflection": config.get("reflection", {}).get("enabled"),
            "subagents": config.get("subagents", {}).get("enabled"),
            "max_tool_calls_per_gw": config.get("agent", {}).get("max_tool_calls_per_gw"),
            "rules_version": config.get("simulation", {}).get("rules_version"),
            "dataset_version": config.get("world", {}).get("dataset_version"),
            "git_commit": _git_commit(),
            "tracking_backend": "databricks" if is_databricks_uri(uri) else "local",
        }
        if extra_params:
            params.update(extra_params)
        mlflow.log_params({k: str(v) for k, v in params.items() if v is not None})
        return self.run_id

    def describe(self) -> str:
        return (
            f"uri={self.tracking_uri} experiment={self.experiment_name} "
            f"id={self.experiment_id} run={self.run_id}"
        )

    def log_metrics(self, metrics: dict[str, Any], step: int | None = None) -> None:
        if not self.enabled:
            return
        clean = {}
        for key, value in metrics.items():
            if value is None:
                continue
            try:
                clean[key] = float(value)
            except (TypeError, ValueError):
                continue
        if clean:
            mlflow.log_metrics(clean, step=step)

    def log_artifacts(self, files: list[Path]) -> None:
        if not self.enabled:
            return
        for path in files:
            if path.exists():
                mlflow.log_artifact(str(path))

    def set_tags(self, tags: dict[str, Any]) -> None:
        if not self.enabled:
            return
        mlflow.set_tags({k: str(v) for k, v in tags.items() if v is not None})

    def end(self) -> None:
        if self.enabled and mlflow.active_run():
            mlflow.end_run()
        set_tracing_enabled(False)
        self.enabled = False


def load_yaml(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = repo_root() / resolved
    with resolved.open() as fh:
        return yaml.safe_load(fh)


def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root(),
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"
