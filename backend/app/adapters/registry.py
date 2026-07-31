"""Central receivables lien registry — REAL, not a mock.

This is the duplicate-financing moat: an internal table of active claims on
receivables. Two independent anchors per claim:

- **IRN** — exact match on the government e-invoice ID.
- **Fingerprint** — SHA-256 over the invoice's economic identity
  (app/fingerprint.py), which survives IRN regeneration and cosmetic edits.

The fraud node queries both; accepting a deal writes a lien; repayment
releases it. In production this would federate with the TReDS-interoperable
central registry / CERSAI — the checks themselves are the same queries.
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


def find_active_lien_by_fingerprint(db: Session, fingerprint: str) -> FinancingRegistryEntry | None:
    if not fingerprint:
        return None
    return db.execute(
        select(FinancingRegistryEntry)
        .where(FinancingRegistryEntry.fingerprint == fingerprint,
               FinancingRegistryEntry.status == "active")
    ).scalars().first()


def register_lien(db: Session, irn: str, lender: str, ref: str,
                  fingerprint: str = "") -> FinancingRegistryEntry:
    entry = FinancingRegistryEntry(
        irn=irn, fingerprint=fingerprint, lender=lender, ref=ref,
        financed_on=date.today(), status="active",
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
