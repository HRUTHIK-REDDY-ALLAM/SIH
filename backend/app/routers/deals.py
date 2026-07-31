import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import cache, config
from ..adapters import itfs, registry, settlement
from ..audit import Recorder
from ..auth import get_current_user, require_msme
from ..db import get_db, now_utc
from ..models import FinancingDeal, Invoice, User
from ..pipeline.graph import start_pipeline
from ..serialize import fmt_date, inr, inr_compact, irn_short, serialize_deal
from .consents import active_consents

router = APIRouter(tags=["deals"])

BLOCKING_STATUSES = ("running", "approved", "conditional", "manual_review", "financed")


class DealRequest(BaseModel):
    invoice_id: int = Field(gt=0, description="ID of a pending invoice owned by the caller")


@router.post("/deals", status_code=201)
def create_deal(body: DealRequest, user: User = Depends(require_msme),
                db: Session = Depends(get_db)):
    invoice = db.get(Invoice, body.invoice_id)
    if invoice is None or invoice.msme_id != user.msme_id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status != "pending":
        raise HTTPException(status_code=409, detail=f"Invoice is already {invoice.status}")

    existing = db.execute(
        select(FinancingDeal).where(
            FinancingDeal.invoice_id == invoice.id,
            FinancingDeal.status.in_(BLOCKING_STATUSES),
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=409,
                            detail=f"A deal for this invoice is already {existing.status} (deal #{existing.id})")

    # Real consent enforcement at the API boundary (the pipeline re-checks too).
    granted = {c.ctype for c in active_consents(db, user.msme_id)}
    missing = {"gst", "aa"} - granted
    if missing:
        labels = {"gst": "GST data", "aa": "bank data via Account Aggregator"}
        raise HTTPException(status_code=403,
                            detail="Consent required before underwriting: "
                                   + " and ".join(labels[m] for m in sorted(missing)))

    deal = FinancingDeal(invoice_id=invoice.id, msme_id=user.msme_id, status="running")
    db.add(deal)
    db.commit()
    start_pipeline(deal.id)
    return {"deal_id": deal.id}


def _load_deal(db: Session, deal_id: int, user: User) -> FinancingDeal:
    deal = db.get(FinancingDeal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    if user.role == "msme" and deal.msme_id != user.msme_id:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.get("/deals/{deal_id}")
def get_deal(deal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    deal = _load_deal(db, deal_id, user)
    if deal.status != "running":
        cached = cache.get_cached_deal(deal.id)
        if cached is not None:
            return json.loads(cached)
    payload = serialize_deal(db, deal)
    if deal.status != "running":
        cache.cache_deal(deal.id, json.dumps(payload))
    return payload


@router.post("/deals/{deal_id}/accept")
def accept_deal(deal_id: int, user: User = Depends(require_msme), db: Session = Depends(get_db)):
    deal = _load_deal(db, deal_id, user)
    if deal.status not in ("approved", "conditional"):
        raise HTTPException(status_code=409, detail=f"Deal is {deal.status} — offer cannot be accepted")

    invoice = deal.invoice
    rec = Recorder(db, deal.id)

    # 1. Place the deal with the licensed financier via the ITFS platform (mock).
    placement = itfs.place_deal(deal_id=deal.id, amount=deal.advance_amount,
                                msme_name=user.msme.short_name, score=deal.score)
    # 2. Register the lien in the central registry (real — this is what the
    #    fraud node queries on every future request).
    lien_ref = f"VS-{deal.id:05d}"
    registry.register_lien(db, invoice.irn, config.OUR_LENDER, lien_ref,
                           fingerprint=invoice.fingerprint)
    # 3. Disburse over the (mock) payment rails.
    payout = settlement.disburse(deal_id=deal.id, amount=deal.net_amount,
                                 account=user.msme.bank_account)

    invoice.status = "financed"
    deal.status = "financed"
    deal.financed_at = now_utc()
    decision = dict(deal.decision or {})
    st = dict(decision.get("settlement") or {})
    st.update({"utr": payout["utr"], "rail": payout["rail"], "account": payout["account"],
               "itfsRef": placement["platform_ref"], "itfsPlatform": placement["platform"]})
    decision["settlement"] = st
    deal.decision = decision
    db.commit()
    cache.invalidate_deal(deal.id)

    rec.settlement(f"Offer accepted · placed on {placement['platform']} — accepted by "
                   f"{placement['financier']} (ref {placement['platform_ref']})")
    rec.settlement(f"Lien registered on {irn_short(invoice.irn)} by {config.OUR_LENDER} "
                   f"(ref {lien_ref} · fingerprint {invoice.fingerprint[:10]}…)")
    rec.settlement(f"Disbursing {inr(deal.net_amount)} to {user.msme.bank_account} via {payout['rail']} — "
                   f"{payout['utr']}")
    return serialize_deal(db, deal)


@router.post("/deals/{deal_id}/request-review")
def request_review(deal_id: int, user: User = Depends(require_msme), db: Session = Depends(get_db)):
    deal = _load_deal(db, deal_id, user)
    if deal.status != "conditional":
        raise HTTPException(status_code=409, detail=f"Deal is {deal.status} — manual review not applicable")
    deal.status = "manual_review"
    db.commit()
    cache.invalidate_deal(deal.id)
    Recorder(db, deal.id).override("Exporter requested manual review — routed to the Nexa Capital credit desk.")
    return serialize_deal(db, deal)


# ------------------------------------------------------------- dashboard ----
STATUS_DETAIL = {
    "running": "Underwriting in progress",
    "approved": "Offer ready — awaiting your acceptance",
    "conditional": "Conditional offer available — tap to view",
    "manual_review": "With the Nexa Capital credit desk for manual review",
    "error": "Run failed — request financing again",
}


@router.get("/dashboard")
def dashboard(user: User = Depends(require_msme), db: Session = Depends(get_db)):
    msme = user.msme
    deals = db.execute(
        select(FinancingDeal).where(FinancingDeal.msme_id == msme.id)
        .order_by(FinancingDeal.created_at.desc())
    ).scalars().all()

    financed_total = sum(d.advance_amount or 0 for d in deals if d.status in ("financed", "repaid"))
    n_funded = sum(1 for d in deals if d.status in ("financed", "repaid"))
    decided = [d for d in deals if d.decided_at is not None]
    if decided:
        avg_s = sum((d.decided_at - d.created_at).total_seconds() for d in decided) / len(decided)
        avg_str = f"{int(avg_s // 60)}m {int(avg_s % 60):02d}s"
    else:
        avg_str = "—"
    repaid = [d for d in deals if d.status == "repaid" and d.repaid_at is not None]
    on_time = sum(1 for d in repaid if d.repaid_at.date() <= d.invoice.due_on)
    on_time_str = f"{on_time / len(repaid):.0%}" if repaid else "—"

    stats = [
        {"label": "Financed till date", "value": inr_compact(financed_total) if financed_total else "₹0",
         "sub": f"{n_funded} deals funded"},
        {"label": "Avg. decision time", "value": avg_str, "sub": "vs 15–21 days traditional"},
        {"label": "On-time settlements", "value": on_time_str, "sub": f"{on_time} of {len(repaid)} repaid deals"},
    ]

    rows = []
    for d in deals:
        inv = d.invoice
        if d.status == "repaid":
            detail = f"Financed {fmt_date(d.financed_at.date())} · settled {fmt_date(d.repaid_at.date())}"
        elif d.status == "financed":
            detail = (f"Financed {fmt_date(d.financed_at.date())} · buyer pays {fmt_date(inv.due_on)} · "
                      f"balance {inr(inv.amount - (d.advance_amount or 0))} on settlement")
        elif d.status == "declined":
            headline = (d.decision or {}).get("headline", "Declined")
            detail = f"{headline} · {fmt_date(d.decided_at.date()) if d.decided_at else ''}"
        else:
            detail = STATUS_DETAIL.get(d.status, d.status)
        rows.append({
            "deal_id": d.id, "code": inv.code, "buyer": inv.buyer.name,
            "amount": inv.amount, "status": d.status, "detail": detail,
            "openable": d.status in ("approved", "conditional", "manual_review"),
        })

    return {
        "company": {"name": msme.name, "short": msme.short_name, "city": msme.city,
                    "gstin": msme.gstin, "iec": msme.iec, "sector": msme.sector,
                    "bank": msme.bank_account, "kyc": msme.kyc_status},
        "stats": stats,
        "deals": rows,
    }
