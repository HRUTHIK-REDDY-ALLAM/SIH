import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite by default; swap for a postgres:// URL without touching any other code.
DATABASE_URL = os.environ.get("TB_DATABASE_URL", f"sqlite:///{BASE_DIR / 'tradebridge.db'}")

# Multiplier on the pipeline's per-line delays. 1.0 = demo pacing (a run takes
# ~12s so judges can watch it stream); set TB_PACING=0 for instant runs/tests.
PACING = float(os.environ.get("TB_PACING", "1.0"))

APP_NAME = "TradeBridge AI"
OUR_LENDER = "Nexa Capital NBFC Ltd."

# Delegated lending mandate enforced by the compliance node.
MANDATE_MAX_EXPOSURE = 2_500_000  # ₹25L total live exposure per exporter
MANDATE_MAX_TENOR_DAYS = 90

# Advance/pricing policy applied by the risk-scoring node.
SCORE_APPROVE_MIN = 75   # score >= 75  -> approve at 80%
SCORE_CONDITIONAL_MIN = 45  # 45..74 -> conditional at 50%; below -> decline
