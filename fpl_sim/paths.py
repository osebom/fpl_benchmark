from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def repo_root() -> Path:
    return REPO_ROOT


def data_dir() -> Path:
    override = os.environ.get("FPL_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return (REPO_ROOT / "final_fpl").resolve()


def configs_dir() -> Path:
    return REPO_ROOT / "configs"
