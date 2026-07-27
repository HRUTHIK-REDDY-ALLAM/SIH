# MOCK ADAPTER — no production credentials available.
# Production swap: an RBI Account Aggregator (Sahamati ecosystem) FIU
# integration; the consent_ref would be a real AA consent artefact ID. The
# interface deliberately requires the consent reference so consent enforcement
# survives the swap.
from .. import demo_world


class ConsentRequired(Exception):
    pass


def fetch_bank_summary(account: str, *, consent_ref: str) -> dict | None:
    """Return a 12-month bank statement summary. Refuses without a consent ref —
    the same contract a real AA fetch has."""
    if not consent_ref:
        raise ConsentRequired("Account Aggregator fetch requires an active consent reference")
    return demo_world.BANK_SUMMARIES.get(account)
