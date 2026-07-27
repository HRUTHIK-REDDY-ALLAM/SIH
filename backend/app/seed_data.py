"""Seeds the database with the three deterministic demo scenarios.

- Invoice A (Meridian, ₹20L): clean file -> the pipeline approves at 80%.
- Invoice B (Straits, ₹34L): an ACTIVE LIEN row exists in financing_registry
  (financed by Apex Trade Capital) -> the fraud node genuinely finds it.
- Invoice C (Lion City, ₹8.5L): buyer is 17 months old with zero rows in
  trade_history -> thin file -> conditional 50%.

Outcomes are not hardcoded anywhere: they emerge from this data.
"""
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from . import demo_world as W
from .auth import hash_password
from .db import Base, engine
from .models import (Buyer, FinancingDeal, FinancingRegistryEntry, Invoice,
                     Msme, TradeHistory, User)

TODAY = date.today()


def _dt(d: date, hh: int = 10, mm: int = 0, ss: int = 0) -> datetime:
    return datetime.combine(d, time(hh, mm, ss))


def reset_schema() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def seed(db: Session) -> None:
    saanvi = Msme(
        name="Saanvi Textiles Exports Pvt. Ltd.", short_name="Saanvi Textiles",
        city="Tiruppur, Tamil Nadu", gstin=W.GSTIN_SAANVI, iec="IEC 0416923847",
        sector="Organic cotton knitwear", bank_account=W.BANK_SAANVI,
        kyc_status="verified", onboarding_status="active",
    )
    db.add(saanvi)

    meridian = Buyer(name="Meridian Textiles Pte. Ltd.", uen=W.UEN_MERIDIAN)
    straits = Buyer(name="Straits Apparel Group Pte. Ltd.", uen=W.UEN_STRAITS)
    lion = Buyer(name="Lion City Trading Pte. Ltd.", uen=W.UEN_LION)
    orchid = Buyer(name="Orchid Lane Retail Pte. Ltd.", uen=W.UEN_ORCHID)
    db.add_all([meridian, straits, lion, orchid])
    db.flush()

    # --- the three demo invoices (status pending) ---------------------------
    inv_a = Invoice(msme_id=saanvi.id, buyer_id=meridian.id, code="INV-2026-0142",
                    irn=W.IRN_A, amount=2_000_000,
                    issued_on=TODAY - timedelta(days=15), due_on=TODAY + timedelta(days=45),
                    goods="300 cartons · organic cotton knitwear", hsn="6109")
    inv_b = Invoice(msme_id=saanvi.id, buyer_id=straits.id, code="INV-2026-0156",
                    irn=W.IRN_B, amount=3_400_000,
                    issued_on=TODAY - timedelta(days=22), due_on=TODAY + timedelta(days=60),
                    goods="520 rolls · dyed cotton fabric", hsn="5208")
    inv_c = Invoice(msme_id=saanvi.id, buyer_id=lion.id, code="INV-2026-0161",
                    irn=W.IRN_C, amount=850_000,
                    issued_on=TODAY - timedelta(days=6), due_on=TODAY + timedelta(days=30),
                    goods="120 cartons · knit t-shirts, pilot order", hsn="6109")
    db.add_all([inv_a, inv_b, inv_c])

    # --- THE FRAUD SEED: invoice B already carries an active lien -----------
    db.add(FinancingRegistryEntry(
        irn=W.IRN_B, lender="Apex Trade Capital NBFC",
        financed_on=TODAY - timedelta(days=13), ref="TRD-2026-88412", status="active",
    ))

    # --- buyer payment history (real rows the pipeline aggregates) ----------
    early_pattern = [2, 1, 3, 2, 1, 2, 2, 1, 3, 2, 1, 2, 2, 1]  # avg 1.8 days early
    for i, early in enumerate(early_pattern):
        due = TODAY - timedelta(days=40 + i * 55)
        db.add(TradeHistory(msme_id=saanvi.id, buyer_id=meridian.id,
                            invoice_code=f"INV-{due.year}-M{i + 1:02d}",
                            amount=900_000 + (i % 5) * 150_000,
                            due_on=due, paid_on=due - timedelta(days=early)))
    for i, early in enumerate([1, 0, 2]):
        due = TODAY - timedelta(days=70 + i * 90)
        db.add(TradeHistory(msme_id=saanvi.id, buyer_id=orchid.id,
                            invoice_code=f"INV-{due.year}-O{i + 1:02d}",
                            amount=700_000 + i * 120_000,
                            due_on=due, paid_on=due - timedelta(days=early)))
    for i, early in enumerate([1, 2, 0]):
        due = TODAY - timedelta(days=120 + i * 75)
        db.add(TradeHistory(msme_id=saanvi.id, buyer_id=straits.id,
                            invoice_code=f"INV-{due.year}-S{i + 1:02d}",
                            amount=1_500_000 + i * 200_000,
                            due_on=due, paid_on=due - timedelta(days=early)))

    # --- three settled historical deals (dashboard history + stats) ---------
    history = [
        ("INV-2026-0128", meridian, 1_420_000, 90, "d1e8f2a04b6c7d8e",
         "Repeat buyer with a spotless record; approved at 80%."),
        ("INV-2026-0135", orchid, 980_000, 69, "d2c7b1e93a5f4d6b",
         "Established buyer; approved at 80%."),
        ("INV-2026-0139", meridian, 1_160_000, 49, "d3a9c4f16e2b8d0c",
         "Repeat buyer with a spotless record; approved at 80%."),
    ]
    for code, buyer, amount, days_ago, irn_stub, why in history:
        created = TODAY - timedelta(days=days_ago)
        repaid = created + timedelta(days=45)
        advance = amount * 80 // 100
        fee = round(advance * 0.0175)
        inv = Invoice(msme_id=saanvi.id, buyer_id=buyer.id, code=code,
                      irn=(irn_stub * 4)[:64], amount=amount,
                      issued_on=created - timedelta(days=5), due_on=repaid,
                      goods="Cotton knitwear export", hsn="6109", status="repaid")
        db.add(inv)
        db.flush()
        db.add(FinancingDeal(
            invoice_id=inv.id, msme_id=saanvi.id, status="repaid",
            score=84, band="Low risk", advance_pct=80, advance_amount=advance,
            fee_amount=fee, net_amount=advance - fee,
            decision={"outcome": "approved", "score": 84, "band": "Low risk",
                      "headline": "Approved (settled)", "advancePct": 80,
                      "advance": advance, "fee": fee, "net": advance - fee,
                      "balance": amount - advance, "feePct": "1.75%",
                      "reasons": [why, "Deal has fully settled — buyer paid on the due date."]},
            created_at=_dt(created), decided_at=_dt(created, 10, 2, 8),
            financed_at=_dt(created, 10, 6), repaid_at=_dt(repaid, 11),
        ))
        db.add(FinancingRegistryEntry(irn=inv.irn, lender="Nexa Capital NBFC Ltd.",
                                      financed_on=created, ref=f"TB-H{code[-4:]}",
                                      status="released"))

    # --- demo accounts ------------------------------------------------------
    db.flush()
    db.add(User(email="demo@saanvi.in", password_hash=hash_password("demo1234"),
                role="msme", msme_id=saanvi.id))
    db.add(User(email="fin@nexacapital.in", password_hash=hash_password("demo1234"),
                role="financier"))
    db.commit()
