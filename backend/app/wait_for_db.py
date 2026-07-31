"""Block until the database accepts connections (Docker Compose start order)."""
import sys
import time

from sqlalchemy import text

from .config import DATABASE_URL
from .db import engine

DEADLINE_SECONDS = 60


def main() -> int:
    if DATABASE_URL.startswith("sqlite"):
        return 0
    started = time.monotonic()
    while time.monotonic() - started < DEADLINE_SECONDS:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"database ready after {time.monotonic() - started:.1f}s")
            return 0
        except Exception as exc:  # not up yet
            print(f"waiting for database… ({type(exc).__name__})")
            time.sleep(2)
    print("database did not become ready in time", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
