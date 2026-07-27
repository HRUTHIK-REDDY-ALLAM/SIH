from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config
from ..adapters import registry, settlement
from ..audit import Recorder
from ..auth import require_financier
from ..db import get_db, now_utc
from ..models import FinancingDeal, User
from ..serialize import fmt_date, inr, serialize_deal

router = APIRouter(prefix="/financier", tags=["financier"])


def _facts(db: Session, deal: FinancingDeal) -> list[list[str]]:
    f = deal.features or {}
    inv = deal.invoice
    decision = deal.decision or {}
    if decision.get("evidence"):
        ev = decision["evidence"]
        lien_fact = f"MATCH — {ev['lender']} ({ev['financedOn']})"
    else:
        lien_fact = "Clean — no prior pledge at underwriting time"
    gst = (f"₹{f['turnover_cr']} Cr · {f['gst_filings_on_time']}/{f['gst_filings_total']} filings on time"
           if f.get("turnover_cr") else "—")
    bank = (f"{inr(f['avg_monthly_credits'])} avg monthly · {f.get('bounced_cheques', 0)} bounces"
            if f.get("avg_monthly_credits") else "—")
    return [
        ["Exporter", deal.msme.name],
        ["GST profile", gst],
        ["Bank inflows", bank],
        ["Buyer", inv.buyer.name],
        ["Invoice", f"{inr(inv.amount)} · due {fmt_date(inv.due_on)}"],
        ["Lien registry", lien_fact],
    ]


@router.get("/deals")
def list_deals(user: User = Depends(require_financier), db: Session = Depends(get_db)):
    deals = db.execute(
        select(FinancingDeal).order_by(FinancingDeal.created_at.desc())
    ).scalars().all()
    payload = []
    for deal in deals:
        item = serialize_deal(db, deal)
        item["msme"] = deal.msme.name
        item["facts"] = _facts(db, deal)
        payload.append(item)
    return {
        "mandate": {"lender": config.OUR_LENDER,
                    "text": f"Auto-disburse when: score ≥ {config.SCORE_APPROVE_MIN} · "
                            f"exposure ≤ {inr(config.MANDATE_MAX_EXPOSURE)} · "
                            f"tenor ≤ {config.MANDATE_MAX_TENOR_DAYS} days"},
        "deals": payload,
    }


class OverrideRequest(BaseModel):
    action: str
    note: str = Field(default="", max_length=500)


@router.post("/deals/{deal_id}/override")
def override_deal(deal_id: int, body: OverrideRequest,
                  user: User = Depends(require_financier), db: Session = Depends(get_db)):
    deal = db.get(FinancingDeal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    if body.action not in ("approve", "decline"):
        raise HTTPException(status_code=422, detail="action must be 'approve' or 'decline'")

    allowed = {"approve": ("manual_review", "conditional"),
               "decline": ("manual_review", "conditional", "approved")}
    if deal.status not in allowed[body.action]:
        raise HTTPException(status_code=409,
                            detail=f"Cannot {body.action} a deal in status '{deal.status}'")

    deal.status = "approved" if body.action == "approve" else "declined"
    deal.override_note = body.note or None
    decision = dict(deal.decision or {})
    decision["overridden"] = {"action": body.action, "by": f"{config.OUR_LENDER} deal desk",
                              "note": body.note, "at": now_utc().isoformat()}
    if body.action == "approve":
        decision["banner"] = "Approved by the financier's credit desk after manual review."
    deal.decision = decision
    db.commit()
    Recorder(db, deal.id).override(
        f"Manual override by {user.email}: {body.action.upper()}"
        + (f" — “{body.note}”" if body.note else ""))
    item = serialize_deal(db, deal)
    item["msme"] = deal.msme.name
    item["facts"] = _facts(db, deal)
    return item


@router.post("/deals/{deal_id}/simulate-repayment")
def simulate_repayment(deal_id: int, user: User = Depends(require_financier),
                       db: Session = Depends(get_db)):
    deal = db.get(FinancingDeal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    if deal.status != "financed":
        raise HTTPException(status_code=409, detail=f"Deal is {deal.status} — nothing to repay")

    inv = deal.invoice
    rec = Recorder(db, deal.id)
    receipt = settlement.collect_repayment(deal_id=deal.id, amount=inv.amount, payer=inv.buyer.name)
    registry.release_lien(db, inv.irn, config.OUR_LENDER)
    inv.status = "repaid"
    deal.status = "repaid"
    deal.repaid_at = now_utc()
    db.commit()

    balance = inv.amount - (deal.advance_amount or 0)
    rec.settlement(f"Buyer payment received — {inv.buyer.name} paid {inr(inv.amount)} into escrow "
                   f"({receipt['utr']})")
    rec.settlement(f"Advance auto-recovered by {config.OUR_LENDER}: {inr(deal.advance_amount or 0)}")
    rec.settlement(f"Balance released to {deal.msme.short_name}: {inr(balance)} · lien released")
    item = serialize_deal(db, deal)
    item["msme"] = deal.msme.name
    item["facts"] = _facts(db, deal)
    return item
