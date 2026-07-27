"""Central receivables lien registry — REAL, not a mock.

This is the duplicate-financing moat: an internal table of active claims on
receivables (by IRN). The fraud node queries it; accepting a deal writes to it;
repayment releases it. In production this would federate with the
TReDS-interoperable central registry / CERSAI, but the check itself is the
same query against the same kind of table.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import FinancingRegistryEntry


def find_active_lien(db: Session, irn: str) -> FinancingRegistryEntry | None:
    return db.execute(
        select(FinancingRegistryEntry)
        .where(FinancingRegistryEntry.irn == irn, FinancingRegistryEntry.status == "active")
    ).scalars().first()


def register_lien(db: Session, irn: str, lender: str, ref: str) -> FinancingRegistryEntry:
    entry = FinancingRegistryEntry(
        irn=irn, lender=lender, ref=ref, financed_on=date.today(), status="active"
    )
    db.add(entry)
    db.commit()
    return entry


def release_lien(db: Session, irn: str, lender: str) -> bool:
    entry = db.execute(
        select(FinancingRegistryEntry).where(
            FinancingRegistryEntry.irn == irn,
            FinancingRegistryEntry.lender == lender,
            FinancingRegistryEntry.status == "active",
        )
    ).scalars().first()
    if entry is None:
        return False
    entry.status = "released"
    db.commit()
    return True
