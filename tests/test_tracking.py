from fpl_sim.tracking.mlflow_tracker import is_databricks_uri, resolve_experiment, resolve_tracking_uri


def test_databricks_uri_from_host_and_token(monkeypatch):
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    monkeypatch.setenv("DATABRICKS_HOST", "https://example.cloud.databricks.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "dapi-test")
    assert resolve_tracking_uri() == "databricks"
    assert is_databricks_uri("databricks")
    assert is_databricks_uri("databricks://myprofile")


def test_explicit_uri_wins(monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "databricks")
    monkeypatch.setenv("DATABRICKS_HOST", "https://example.cloud.databricks.com")
    assert resolve_tracking_uri() == "databricks"


def test_experiment_id_wins(monkeypatch):
    monkeypatch.setenv("MLFLOW_EXPERIMENT_ID", "12345")
    monkeypatch.setenv("MLFLOW_EXPERIMENT_NAME", "/Shared/other")
    exp_id, exp_name = resolve_experiment({}, "databricks")
    assert exp_id == "12345"
    assert exp_name == "/Shared/other"


def test_databricks_prefixes_shared_path(monkeypatch):
    monkeypatch.delenv("MLFLOW_EXPERIMENT_ID", raising=False)
    monkeypatch.delenv("MLFLOW_EXPERIMENT_NAME", raising=False)
    _, name = resolve_experiment({"experiment": {"name": "command_a_plus_baseline_v1"}}, "databricks")
    assert name == "/Shared/command_a_plus_baseline_v1"


def test_config_path_kept(monkeypatch):
    monkeypatch.delenv("MLFLOW_EXPERIMENT_ID", raising=False)
    monkeypatch.delenv("MLFLOW_EXPERIMENT_NAME", raising=False)
    _, name = resolve_experiment(
        {"tracking": {"experiment_name": "/Shared/fpl_sim"}},
        "databricks",
    )
    assert name == "/Shared/fpl_sim"
