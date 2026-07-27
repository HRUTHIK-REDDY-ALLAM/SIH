from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import require_msme
from ..db import get_db
from ..models import Invoice, User
from ..serialize import serialize_invoice

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("")
def list_invoices(user: User = Depends(require_msme), db: Session = Depends(get_db)):
    invoices = db.execute(
        select(Invoice)
        .where(Invoice.msme_id == user.msme_id, Invoice.status == "pending")
        .order_by(Invoice.code)
    ).scalars().all()
    return [serialize_invoice(db, inv) for inv in invoices]
