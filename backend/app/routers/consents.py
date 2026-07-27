import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import require_msme
from ..db import get_db, now_utc
from ..models import Consent, User

router = APIRouter(prefix="/consents", tags=["consents"])

SCOPES = {
    "gst": "GSTR-1 & GSTR-3B summaries · last 24 months · read-only · via licensed GSP",
    "aa": "12-month bank statement summary · one-time fetch · RBI Account Aggregator (Sahamati) · DEPA-compliant",
}


class ConsentRequest(BaseModel):
    ctype: str


def _serialize(c: Consent) -> dict:
    return {
        "ctype": c.ctype,
        "status": c.status,
        "consent_ref": c.consent_ref,
        "scope": c.scope,
        "granted_on": c.granted_at.strftime("%d %b %Y"),
        "expires_on": c.expires_at.strftime("%d %b %Y"),
    }


def active_consents(db: Session, msme_id: int) -> list[Consent]:
    return list(db.execute(
        select(Consent).where(
            Consent.msme_id == msme_id,
            Consent.status == "active",
            Consent.expires_at > now_utc(),
        )
    ).scalars())


@router.get("")
def list_consents(user: User = Depends(require_msme), db: Session = Depends(get_db)):
    return [_serialize(c) for c in active_consents(db, user.msme_id)]


@router.post("", status_code=201)
def grant_consent(body: ConsentRequest, user: User = Depends(require_msme),
                  db: Session = Depends(get_db)):
    if body.ctype not in SCOPES:
        raise HTTPException(status_code=422, detail="ctype must be 'gst' or 'aa'")
    existing = [c for c in active_consents(db, user.msme_id) if c.ctype == body.ctype]
    if existing:
        return _serialize(existing[0])
    prefix = "GSP" if body.ctype == "gst" else "AA"
    consent = Consent(
        msme_id=user.msme_id, ctype=body.ctype,
        consent_ref=f"{prefix}-{now_utc():%Y}-{secrets.token_hex(2).upper()}",
        scope=SCOPES[body.ctype],
        expires_at=now_utc() + timedelta(days=30),
    )
    db.add(consent)
    db.commit()
    return _serialize(consent)
