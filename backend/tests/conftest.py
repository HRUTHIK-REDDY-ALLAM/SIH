"""Test configuration — MUST set env before any app import, because config
reads the environment at import time."""
import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parent / "test_vittsetu.db"
os.environ["VS_DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["VS_PACING"] = "0"          # instant pipeline runs
os.environ["VS_DISABLE_LLM"] = "1"     # never call out during tests
os.environ.pop("REDIS_URL", None)      # force the in-memory cache fallback

import pytest  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.seed_data import reset_schema, seed  # noqa: E402


@pytest.fixture()
def db():
    reset_schema()
    session = SessionLocal()
    try:
        seed(session)
        yield session
    finally:
        session.close()
