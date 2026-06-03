from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
MIGRATIONS_DIR = ROOT_DIR / "migrations"
DATABASE_PATH = DATA_DIR / "jobfit.db"
CREDENTIALS_DIR = ROOT_DIR / "credentials"
GMAIL_CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"
GMAIL_TOKEN_PATH = CREDENTIALS_DIR / "token.json"

