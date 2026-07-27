from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import now_utc
from .models import AuditEvent, FinancingDeal, Invoice, TradeHistory
from .pipeline import NODE_DEFS


def inr(n) -> str:
    """Indian-style grouping: 1600000 -> ₹16,00,000."""
    s = str(int(round(n)))
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        s = ",".join([head] + groups + [tail])
    return ("-₹" if neg else "₹") + s


def inr_compact(n) -> str:
    if n >= 10_000_000:
        return f"₹{n / 10_000_000:.2f} Cr"
    return f"₹{n / 100_000:.1f}L"


def fmt_date(d: date) -> str:
    return d.strftime("%d %b %Y")


def irn_short(irn: str) -> str:
    return f"IRN {irn[:6]}…{irn[-4:]}" if len(irn) > 12 else f"IRN {irn}"


def relationship_count(db: Session, msme_id: int, buyer_id: int) -> int:
    return db.execute(
        select(func.count(TradeHistory.id))
        .where(TradeHistory.msme_id == msme_id, TradeHistory.buyer_id == buyer_id)
    ).scalar() or 0


def invoice_tag(rel_count: int, amount: int) -> tuple[str, str]:
    if rel_count == 0:
        return "New buyer · first order", "amber"
    if rel_count >= 8:
        return f"Repeat buyer · {rel_count} prior shipments", "blue"
    if amount >= 3_000_000:
        return "Large order", "slate"
    return f"{rel_count} prior shipments", "slate"


def serialize_invoice(db: Session, inv: Invoice) -> dict:
    rel = relationship_count(db, inv.msme_id, inv.buyer_id)
    tag, tone = invoice_tag(rel, inv.amount)
    tenor_days = (inv.due_on - inv.issued_on).days
    return {
        "id": inv.id,
        "code": inv.code,
        "amount": inv.amount,
        "issued": fmt_date(inv.issued_on),
        "due": fmt_date(inv.due_on),
        "tenor": f"{tenor_days}-day tenor",
        "goods": inv.goods,
        "irn": irn_short(inv.irn),
        "status": inv.status,
        "tag": tag,
        "tagTone": tone,
        "buyer": {"name": inv.buyer.name, "uen": f"UEN {inv.buyer.uen}", "country": inv.buyer.country},
    }


def _events(db: Session, deal_id: int) -> list[AuditEvent]:
    return list(db.execute(
        select(AuditEvent).where(AuditEvent.deal_id == deal_id).order_by(AuditEvent.seq)
    ).scalars())


def build_steps(events: list[AuditEvent], deal: FinancingDeal) -> list[dict]:
    by_node: dict[str, dict] = {}
    for ev in events:
        if ev.event == "node_start":
            by_node[ev.node] = {"status": "running", "finding": None}
        elif ev.event == "node_complete":
            by_node[ev.node] = {"status": ev.status, "finding": ev.message}

    halted = any(s["status"] == "flagged" for s in by_node.values())
    finished = deal.status != "running"
    steps = []
    for node_id, title, caption in NODE_DEFS:
        info = by_node.get(node_id)
        if info is None:
            status = "skipped" if (halted or finished) else "pending"
            info = {"status": status, "finding": None}
        steps.append({"id": node_id, "title": title, "caption": caption, **info})
    return steps


def build_trace(events: list[AuditEvent], deal: FinancingDeal) -> list[dict]:
    lines = []
    for ev in events:
        if ev.event in ("line", "sys", "settlement", "override"):
            ts = (ev.created_at - deal.created_at).total_seconds()
            lines.append({"ts": f"{max(ts, 0):.1f}", "k": ev.kind or "sys", "text": ev.message})
    return lines


def serialize_deal(db: Session, deal: FinancingDeal, include_trace: bool = True) -> dict:
    events = _events(db, deal.id)
    end = deal.decided_at or now_utc()
    payload = {
        "deal": {
            "id": deal.id,
            "status": deal.status,
            "score": deal.score,
            "band": deal.band,
            "elapsed": max(int((end - deal.created_at).total_seconds()), 0),
            "created_at": deal.created_at.isoformat(),
            "override_note": deal.override_note,
        },
        "invoice": serialize_invoice(db, deal.invoice),
        "steps": build_steps(events, deal),
        "decision": deal.decision,
    }
    if include_trace:
        payload["trace"] = build_trace(events, deal)
    return payload
