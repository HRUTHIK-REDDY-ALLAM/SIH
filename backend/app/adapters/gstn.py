# MOCK ADAPTER — no production credentials available.
# Production swap: GSTN e-invoice registry (IRP) lookups via a licensed GSP,
# and GSTR-1/3B summaries via the GST returns API. Keep this interface; only
# the data source changes.
from dataclasses import dataclass
from datetime import date

from .. import demo_world


@dataclass
class IrnRecord:
    irn: str
    gstin: str
    buyer_uen: str
    amount: int
    registered_on: date
    signed: bool


def verify_irn(irn: str) -> IrnRecord | None:
    """Look up an IRN on the (synthetic) government e-invoice registry."""
    rec = demo_world.IRN_REGISTRY.get(irn)
    if rec is None:
        return None
    return IrnRecord(irn=irn, **rec)


def get_gst_profile(gstin: str) -> dict | None:
    """Return GSTR filing history + reported turnover for a GSTIN."""
    return demo_world.GST_PROFILES.get(gstin)


def counterparty_graph(gstin: str) -> dict:
    """Linked-entity graph used for circular-trade scanning."""
    return demo_world.COUNTERPARTY_GRAPH.get(gstin, {"linked_entities": 0, "circular_pairs": []})
