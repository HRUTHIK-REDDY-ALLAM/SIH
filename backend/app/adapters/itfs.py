# MOCK ADAPTER — no production credentials available.
# Production swap: a GIFT City ITFS (International Trade Financing Services)
# platform integration, where licensed financiers bid on / accept receivables
# and the platform orchestrates disbursement. VittSetu is the decisioning
# layer; the ITFS platform + NBFC is where the actual lending happens.
import secrets

from ..config import ITFS_PLATFORM, OUR_LENDER


def place_deal(*, deal_id: int, amount: int, msme_name: str, score: int | None) -> dict:
    """Place an underwritten deal on the ITFS platform for financier acceptance."""
    return {
        "platform": ITFS_PLATFORM,
        "platform_ref": f"ITFS-GC-{deal_id:04d}-{secrets.token_hex(2).upper()}",
        "financier": OUR_LENDER,
        "status": "accepted",
        "note": f"Accepted under delegated mandate for {msme_name}"
                + (f" (agent score {score}/100)" if score is not None else ""),
    }
