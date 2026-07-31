"""Proves the load-bearing claims: the duplicate catch is real (IRN AND
fingerprint anchored), the circular-trade graph scan halts loops, consent is
enforced inside the pipeline, the Shapley attribution actually sums to the
score, and the compliance retriever grounds on the right passages."""
from datetime import timedelta

from sqlalchemy import select

from app import demo_world as W
from app.db import now_utc
from app.fingerprint import invoice_fingerprint
from app.models import Buyer, Consent, FinancingDeal, Invoice, Msme, TradeLink
from app.pipeline.graph import run_pipeline
from app.pipeline.retriever import get_retriever
from app.seed_data import TODAY


def _grant_consents(db, msme_id):
    for ctype, ref in (("gst", "GSP-TEST-0001"), ("aa", "AA-TEST-0001")):
        db.add(Consent(msme_id=msme_id, ctype=ctype, consent_ref=ref,
                       scope="test", expires_at=now_utc() + timedelta(days=30)))
    db.commit()


def _run(db, invoice_code):
    invoice = db.execute(select(Invoice).where(Invoice.code == invoice_code)).scalars().one()
    deal = FinancingDeal(invoice_id=invoice.id, msme_id=invoice.msme_id, status="running")
    db.add(deal)
    db.commit()
    run_pipeline(deal.id)
    db.expire_all()
    deal = db.get(FinancingDeal, deal.id)
    assert deal.status != "error", f"pipeline errored: {deal.error}"
    return deal


def _msme(db) -> Msme:
    return db.execute(select(Msme)).scalars().one()


def test_scenario_a_approves_with_correct_numbers(db):
    _grant_consents(db, _msme(db).id)
    deal = _run(db, "INV-2026-0142")
    assert deal.status == "approved"
    d = deal.decision
    assert d["outcome"] == "approved"
    assert d["advance"] == 1_600_000 and d["fee"] == 28_000 and d["net"] == 1_572_000
    assert deal.score >= 75
    assert len(d["citations"]) >= 3  # RAG grounding rode along


def test_scenario_b_duplicate_caught_by_irn_and_fingerprint(db):
    _grant_consents(db, _msme(db).id)
    deal = _run(db, "INV-2026-0156")
    assert deal.status == "declined"
    ev = deal.decision["evidence"]
    assert ev["lender"] == "Apex Trade Capital NBFC"
    assert ev["ref"] == "TRD-2026-88412"
    assert "IRN" in ev["matchedBy"] and "fingerprint" in ev["matchedBy"]


def test_resubmitted_invoice_caught_by_fingerprint_alone(db):
    """The moat's second anchor: same economic invoice, regenerated IRN and new
    invoice number — the IRN lookup misses, the fingerprint lookup catches."""
    msme = _msme(db)
    _grant_consents(db, msme.id)
    straits = db.execute(select(Buyer).where(Buyer.uen == W.UEN_STRAITS)).scalars().one()
    original = db.execute(select(Invoice).where(Invoice.code == "INV-2026-0156")).scalars().one()

    new_irn = "e" * 64  # a fresh IRN the lien registry has never seen
    W.IRN_REGISTRY[new_irn] = {  # the fraudster genuinely re-registered it on the IRP
        "gstin": msme.gstin, "buyer_uen": straits.uen, "amount": original.amount,
        "registered_on": original.issued_on, "signed": True,
    }
    try:
        resub = Invoice(
            msme_id=msme.id, buyer_id=straits.id, code="INV-2026-0199", irn=new_irn,
            fingerprint=invoice_fingerprint(gstin=msme.gstin, buyer_uen=straits.uen,
                                            amount=original.amount, issued_on=original.issued_on),
            amount=original.amount, issued_on=original.issued_on, due_on=original.due_on,
            goods="Reworded goods description", hsn="5208",
        )
        db.add(resub)
        db.commit()
        deal = _run(db, "INV-2026-0199")
    finally:
        W.IRN_REGISTRY.pop(new_irn, None)

    assert deal.status == "declined"
    ev = deal.decision["evidence"]
    assert "resubmission" in ev["matchedBy"]
    assert ev["lender"] == "Apex Trade Capital NBFC"


def test_circular_trade_loop_halts_the_deal(db):
    """Close a loop through this deal's parties and the graph scan must halt it."""
    msme = _msme(db)
    _grant_consents(db, msme.id)
    db.add(TradeLink(src=W.UEN_MERIDIAN, dst=msme.gstin, kind="financing"))
    db.commit()
    deal = _run(db, "INV-2026-0142")  # scenario A would otherwise approve
    assert deal.status == "declined"
    assert deal.decision["headline"].startswith("Declined — circular trading")
    assert "→" in deal.decision["evidence"]["status"]


def test_scenario_c_conditional_at_50(db):
    _grant_consents(db, _msme(db).id)
    deal = _run(db, "INV-2026-0161")
    assert deal.status == "conditional"
    d = deal.decision
    assert d["advancePct"] == 50 and d["advance"] == 425_000 and d["fee"] == 10_200


def test_consent_is_enforced_inside_the_pipeline(db):
    deal = _run(db, "INV-2026-0142")  # no consents granted
    assert deal.status == "declined"
    assert "halted" in deal.decision["headline"].lower()


def test_shapley_attribution_sums_to_the_score(db):
    _grant_consents(db, _msme(db).id)
    deal = _run(db, "INV-2026-0142")
    attr = deal.decision["attribution"]
    total = attr["baseValue"] + sum(c["phi"] for c in attr["contributions"])
    assert abs(total - deal.score) < 1.0  # exact up to per-term rounding
    assert len(attr["contributions"]) == 7


def test_retriever_grounds_fema_and_duplicate_financing():
    r = get_retriever()
    fema = r.search("export value realised repatriated nine months")
    assert fema and fema[0].doc_id == "FEMA-EXP"
    dup = r.search("receivables registry existing lien before financing")
    assert dup and dup[0].doc_id == "DUP-FIN"
