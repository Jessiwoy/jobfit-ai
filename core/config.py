from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
MIGRATIONS_DIR = ROOT_DIR / "migrations"
DATABASE_PATH = DATA_DIR / "jobfit.db"

