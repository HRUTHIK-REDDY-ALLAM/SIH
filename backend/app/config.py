from pathlib import Path

from .secrets import get_secrets_provider

BASE_DIR = Path(__file__).resolve().parent.parent
_secrets = get_secrets_provider()

# SQLite by default so `python run.py` works with zero setup; the Docker
# Compose stack sets VS_DATABASE_URL to PostgreSQL (the system of record).
DATABASE_URL = _secrets.get("VS_DATABASE_URL", f"sqlite:///{BASE_DIR / 'vittsetu.db'}")

# Multiplier on the pipeline's per-line delays. 1.0 = demo pacing (a run takes
# ~13s so judges can watch it stream); set VS_PACING=0 for instant runs/tests.
PACING = float(_secrets.get("VS_PACING", "1.0"))

APP_NAME = "VittSetu"
APP_TAGLINE = "Instant, explainable export finance"
OUR_LENDER = "Nexa Capital NBFC Ltd."
ITFS_PLATFORM = "GIFT City ITFS (International Trade Financing Services)"

# Delegated lending mandate enforced by the compliance node.
MANDATE_MAX_EXPOSURE = 2_500_000  # ₹25L total live exposure per exporter
MANDATE_MAX_TENOR_DAYS = 90
FEMA_REALISATION_DAYS = 270  # 9-month export realisation window (FEMA)

# Advance/pricing policy applied by the risk-scoring node.
SCORE_APPROVE_MIN = 75      # score >= 75 -> approve at 80%
SCORE_CONDITIONAL_MIN = 45  # 45..74 -> conditional at 50%; below -> decline
