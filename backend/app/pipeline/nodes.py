"""The six underwriting nodes. Each is a real function: it calls an adapter or
queries the database, computes features, writes its trace to the audit log, and
returns LangGraph state updates. Nothing here is a hardcoded outcome — the
demo scenarios emerge from the seeded data.
"""
import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import config
from ..adapters import account_aggregator, acra, gstn, registry, sanctions
from ..audit import Recorder
from ..db import now_utc
from ..models import Buyer, Consent, FinancingDeal, Invoice, Msme, TradeHistory
from ..serialize import fmt_date, inr, irn_short
from . import scoring
from .explainer import (build_duplicate_decline, build_offer_decision,
                        build_thin_decline, build_verification_decline)


@dataclass
class PipelineContext:
    db: Session
    rec: Recorder
    deal: FinancingDeal
    invoice: Invoice
    msme: Msme
    buyer: Buyer
    features: dict = field(default_factory=dict)
    lien: object = None
    scored: dict | None = None
    compliance_notes: list[str] = field(default_factory=list)
    mandate_exceeded: bool = False


def _active_consents(ctx: PipelineContext) -> dict[str, Consent]:
    rows = ctx.db.execute(
        select(Consent).where(
            Consent.msme_id == ctx.msme.id,
            Consent.status == "active",
            Consent.expires_at > now_utc(),
        )
    ).scalars()
    return {c.ctype: c for c in rows}


def _relationship_stats(ctx: PipelineContext) -> tuple[int, float, float]:
    rows = ctx.db.execute(
        select(TradeHistory).where(
            TradeHistory.msme_id == ctx.msme.id,
            TradeHistory.buyer_id == ctx.buyer.id,
        )
    ).scalars().all()
    n = len(rows)
    if n == 0:
        return 0, 0.0, 0.0
    on_time = sum(1 for r in rows if r.paid_on <= r.due_on)
    avg_early = sum((r.due_on - r.paid_on).days for r in rows) / n
    return n, on_time / n, avg_early


# ---------------------------------------------------------------- node 1 ----
def data_gathering(ctx: PipelineContext):
    def node(_state: dict) -> dict:
        rec, nid = ctx.rec, "data_gathering"
        rec.node_start(nid)

        # Real consent enforcement: the node refuses to pull data without
        # active consent records, independent of the API-level guard.
        consents = _active_consents(ctx)
        if "gst" not in consents or "aa" not in consents:
            rec.line(nid, "flag", "Missing active data-sharing consent — cannot pull GST/bank data", delay=0.5)
            rec.node_complete(nid, "flagged", "Halted: no active GST/Account Aggregator consent on record.")
            return {"halted": True, "halt_reason": "consent_missing"}

        gst_c, aa_c = consents["gst"], consents["aa"]
        rec.line(nid, "req", f"Requesting GSTR-1 / GSTR-3B summaries for GSTIN {ctx.msme.gstin} "
                             f"(last 24 months) · consent {gst_c.consent_ref}", delay=0.45)
        profile = gstn.get_gst_profile(ctx.msme.gstin)
        if profile is None:
            rec.line(nid, "flag", "GSTIN not found on GST network", delay=0.4)
            rec.node_complete(nid, "flagged", "Halted: GSTIN could not be verified on the GST network.")
            return {"halted": True, "halt_reason": "gstin_unknown"}

        filings = profile["filings"]
        on_time = sum(1 for f in filings if f["on_time"])
        rec.line(nid, "res", f"GST connected — {on_time} of {len(filings)} returns filed on time · "
                             f"reported turnover ₹{profile['turnover_cr']} Cr (+{profile['yoy_growth_pct']}% YoY)",
                 delay=0.5)

        rec.line(nid, "req", f"Fetching 12-month bank summary via Account Aggregator "
                             f"(consent {aa_c.consent_ref})", delay=0.4)
        bank = account_aggregator.fetch_bank_summary(ctx.msme.bank_account, consent_ref=aa_c.consent_ref)
        credits = bank["monthly_credits"]
        avg_credits = statistics.mean(credits)
        stability = round(max(0.0, 1.0 - statistics.pstdev(credits) / avg_credits), 2)
        rec.line(nid, "res", f"Bank data received — avg monthly credits {inr(avg_credits)} · "
                             f"{bank['bounced_cheques_12m']} bounced cheques · EMIs {bank['emi_status']}",
                 delay=0.5)
        rec.line(nid, "calc", f"Cash-flow stability index = {stability:.2f} "
                              f"(σ/μ over 12 monthly inflows)", delay=0.35)

        rel_n, on_time_ratio, avg_early = _relationship_stats(ctx)
        if rel_n == 0:
            rec.line(nid, "warn", f"No settled receivables with {ctx.buyer.name} on record — "
                                  "nothing to benchmark repayment against", delay=0.35)

        ctx.features.update({
            "gst_on_time_ratio": on_time / len(filings),
            "gst_filings_total": len(filings),
            "gst_filings_on_time": on_time,
            "turnover_cr": profile["turnover_cr"],
            "avg_monthly_credits": round(avg_credits),
            "cashflow_stability": stability,
            "bounced_cheques": bank["bounced_cheques_12m"],
            "history_n": rel_n,
            "on_time_ratio": on_time_ratio,
            "avg_days_early": avg_early,
            "concentration": ctx.invoice.amount / avg_credits,
            "consent_refs": {"gst": gst_c.consent_ref, "aa": aa_c.consent_ref},
        })
        finding = (f"Healthy financials: ₹{profile['turnover_cr']} Cr turnover, "
                   f"{on_time}/{len(filings)} on-time GST filings, stable bank inflows.")
        if rel_n == 0:
            finding = (f"Exporter financials healthy (₹{profile['turnover_cr']} Cr turnover, "
                       f"{on_time}/{len(filings)} on-time filings) — but no payment history with this buyer.")
        rec.node_complete(nid, "done", finding)
        return {}

    return node


# ---------------------------------------------------------------- node 2 ----
def invoice_verification(ctx: PipelineContext):
    def node(_state: dict) -> dict:
        rec, nid = ctx.rec, "invoice_verification"
        short = irn_short(ctx.invoice.irn)
        rec.node_start(nid)
        rec.line(nid, "req", f"Querying e-invoice registry (IRP) for {short}", delay=0.45)

        record = gstn.verify_irn(ctx.invoice.irn)
        if record is None:
            rec.line(nid, "flag", "IRN not found on the government registry — invoice cannot be verified",
                     delay=0.5)
            rec.node_complete(nid, "flagged", "IRN does not exist on the e-invoice registry.")
            ctx.deal.decision = build_verification_decline(
                irn_short=short, problem="the IRN does not exist on the registry")
            return {"halted": True, "halt_reason": "invoice_invalid"}

        rec.line(nid, "res", f"IRN found — registered {fmt_date(record.registered_on)} · "
                             f"digitally signed by GSTN", delay=0.5)

        mismatches = []
        if record.amount != ctx.invoice.amount:
            mismatches.append(f"amount (registry {inr(record.amount)} ≠ invoice {inr(ctx.invoice.amount)})")
        if record.gstin != ctx.msme.gstin:
            mismatches.append("seller GSTIN")
        if record.buyer_uen != ctx.buyer.uen:
            mismatches.append("buyer UEN")
        if mismatches:
            rec.line(nid, "flag", "Field mismatch against the registry record: " + ", ".join(mismatches),
                     delay=0.5)
            rec.node_complete(nid, "flagged", "E-invoice fields do not match the registry record.")
            ctx.deal.decision = build_verification_decline(
                irn_short=short, problem="fields do not match the registry record (" + ", ".join(mismatches) + ")")
            return {"halted": True, "halt_reason": "invoice_invalid"}

        rec.line(nid, "calc", f"Matching amount {inr(ctx.invoice.amount)} · buyer {ctx.buyer.name} · "
                              f"seller GSTIN {ctx.msme.gstin} — all fields match", delay=0.4)
        rec.line(nid, "ok", "E-invoice is genuine and unaltered", delay=0.25)
        ctx.features["invoice_verified"] = True
        rec.node_complete(nid, "done", "IRN verified on the government e-invoice registry — every field matches.")
        return {}

    return node


# ---------------------------------------------------------------- node 3 ----
def fraud_check(ctx: PipelineContext):
    def node(_state: dict) -> dict:
        rec, nid = ctx.rec, "fraud_check"
        short = irn_short(ctx.invoice.irn)
        rec.node_start(nid)

        # THE REAL CHECK: query the lien registry table for an active claim.
        rec.line(nid, "req", f"Searching central lien registry for active pledges on {short}", delay=0.45)
        lien = registry.find_active_lien(ctx.db, ctx.invoice.irn)
        if lien is not None:
            ctx.lien = lien
            rec.line(nid, "warn", "Registry returned 1 match — retrieving record…", delay=0.7)
            rec.line(nid, "flag", f"ALERT — active lien found: this invoice was financed by {lien.lender} "
                                  f"on {fmt_date(lien.financed_on)} (ref {lien.ref})", delay=0.8,
                     data={"lender": lien.lender, "ref": lien.ref,
                           "financed_on": lien.financed_on.isoformat()})
            rec.line(nid, "flag", "Duplicate financing detected — the same receivable cannot back two loans",
                     delay=0.55)
            rec.line(nid, "flag", "Declining this request · notifying the financier network · deal logged for review",
                     delay=0.45)
            rec.node_complete(nid, "flagged",
                              f"DUPLICATE FINANCING — already pledged to {lien.lender} on {fmt_date(lien.financed_on)}.")
            ctx.deal.decision = build_duplicate_decline(lien=lien, irn_short=short)
            return {"halted": True, "halt_reason": "duplicate_financing"}

        rec.line(nid, "res", "No lien, assignment or prior financing found on this receivable", delay=0.5)

        graph = gstn.counterparty_graph(ctx.msme.gstin)
        rec.line(nid, "req", f"Scanning counterparty graph ({graph['linked_entities']} linked entities) "
                             "for circular-trade patterns", delay=0.4)
        circular = [p for p in graph["circular_pairs"] if ctx.buyer.uen in p]
        if circular:
            rec.line(nid, "flag", f"Circular trade suspected across {len(circular)} entity pairs", delay=0.5)
            rec.node_complete(nid, "flagged", "Circular-trade pattern detected in the counterparty graph.")
            ctx.deal.decision = build_verification_decline(
                irn_short=short, problem="a circular-trade pattern involves this buyer")
            return {"halted": True, "halt_reason": "circular_trade"}
        rec.line(nid, "res", "No circular flows · no related-party round-tripping detected", delay=0.4)

        # Velocity check — real SQL over this exporter's recent requests.
        recent = ctx.db.execute(
            select(func.count(FinancingDeal.id)).where(
                FinancingDeal.msme_id == ctx.msme.id,
                FinancingDeal.created_at > now_utc() - timedelta(hours=24),
            )
        ).scalar() or 0
        if recent > 4:
            rec.line(nid, "warn", f"Velocity: {recent} financing requests in 24h — noted for the financier",
                     delay=0.3)
            ctx.compliance_notes.append(f"High request velocity: {recent} requests in 24h.")

        ctx.features["fraud_clean"] = True
        rec.line(nid, "ok", "Clean — no duplicate financing, no fraud signals", delay=0.25)
        rec.node_complete(nid, "done", "Invoice is unpledged — no duplicate financing, no circular-trade signals.")
        return {}

    return node


# ---------------------------------------------------------------- node 4 ----
def buyer_verification(ctx: PipelineContext):
    def node(_state: dict) -> dict:
        rec, nid = ctx.rec, "buyer_verification"
        rec.node_start(nid)
        rec.line(nid, "req", f"Looking up UEN {ctx.buyer.uen} on ACRA (Singapore business registry)", delay=0.45)

        company = acra.lookup_company(ctx.buyer.uen)
        if company is None or company["status"] != "Live":
            status = "not found" if company is None else company["status"]
            rec.line(nid, "flag", f"Buyer registration problem — ACRA status: {status}", delay=0.5)
            rec.node_complete(nid, "flagged", f"Buyer could not be verified on ACRA ({status}).")
            ctx.deal.decision = build_verification_decline(
                irn_short=irn_short(ctx.invoice.irn),
                problem=f"the Singapore buyer could not be verified on ACRA ({status})")
            return {"halted": True, "halt_reason": "buyer_unverified"}

        inc = company["incorporated_on"]
        age_months = (date.today().year - inc.year) * 12 + (date.today().month - inc.month)
        rec.line(nid, "res", f"{company['name']} — status Live · incorporated {fmt_date(inc)} "
                             f"({age_months} months ago) · paid-up capital S${company['paid_up_capital_sgd']:,}",
                 delay=0.5)

        hits = sanctions.screen([company["name"], ctx.msme.name])
        if hits:
            rec.line(nid, "flag", f"Sanctions screening hit: {', '.join(hits)}", delay=0.5)
            rec.node_complete(nid, "flagged", "Sanctions screening returned a hit.")
            ctx.deal.decision = build_verification_decline(
                irn_short=irn_short(ctx.invoice.irn), problem="a party failed sanctions screening")
            return {"halted": True, "halt_reason": "sanctions_hit"}

        n, ratio, avg_early = (ctx.features.get("history_n", 0),
                               ctx.features.get("on_time_ratio", 0.0),
                               ctx.features.get("avg_days_early", 0.0))
        thin = n == 0 or age_months < 24
        if n > 0:
            rec.line(nid, "calc", f"Relationship history: {n} settled shipments · {ratio:.0%} on time · "
                                  f"buyer pays on average {avg_early:.1f} days early", delay=0.45)
        else:
            rec.line(nid, "warn", "No payment history with this exporter · no trade references on file yet",
                     delay=0.45)
        if thin and n == 0:
            rec.line(nid, "warn", "Genuine company, but a thin file — treating buyer strength as unproven",
                     delay=0.35)
        else:
            rec.line(nid, "ok", "Established buyer with a verifiable payment record", delay=0.25)

        ctx.features.update({
            "buyer_age_months": age_months,
            "buyer_paid_up_sgd": company["paid_up_capital_sgd"],
            "buyer_incorporated": str(inc.year),
            "buyer_status": company["status"],
        })
        if thin:
            finding = (f"Buyer is real and active — but "
                       + (f"only {age_months} months old, " if age_months < 24 else "")
                       + "with zero payment history with you.")
            rec.node_complete(nid, "warn", finding)
        else:
            rec.node_complete(nid, "done",
                              f"Buyer verified: incorporated {inc.year}, {n} prior shipments, "
                              f"{ratio:.0%} paid on time.")
        return {}

    return node


# ---------------------------------------------------------------- node 5 ----
def risk_scoring(ctx: PipelineContext):
    def node(_state: dict) -> dict:
        rec, nid = ctx.rec, "risk_scoring"
        rec.node_start(nid)
        rec.line(nid, "calc", f"Scoring {len(ctx.features)} signals across exporter health, invoice "
                              "integrity, buyer strength and relationship history", delay=0.5)

        scored = scoring.compute(ctx.features)
        ctx.scored = scored
        comp = scored["components"]
        rec.line(nid, "calc", f"Components — exporter {comp['exporter_health']} · cash-flow {comp['cash_flow']} · "
                              f"buyer {comp['buyer_strength']} · relationship {comp['relationship']} · "
                              f"concentration {comp['concentration_penalty']}", delay=0.5,
                 data=comp)
        rec.line(nid, "calc", f"Composite risk score = {scored['score']} / 100 → {scored['band'].upper()}",
                 delay=0.45)

        if scored["outcome"] == "approved":
            nums_advance = ctx.invoice.amount * scored["advance_pct"] // 100
            rec.line(nid, "ok", f"Decision path: APPROVE — advance {scored['advance_pct']}% "
                                f"({inr(nums_advance)}) at {scored['fee_rate'] * 100:.2f}% flat fee", delay=0.4)
        elif scored["outcome"] == "conditional":
            nums_advance = ctx.invoice.amount * scored["advance_pct"] // 100
            rec.line(nid, "warn", f"Decision path: CONDITIONAL — advance capped at {scored['advance_pct']}% "
                                  f"({inr(nums_advance)}) at {scored['fee_rate'] * 100:.2f}% flat · "
                                  "manual review available", delay=0.4)
        else:
            rec.line(nid, "flag", f"Decision path: DECLINE — score {scored['score']} below financing threshold",
                     delay=0.4)

        rec.node_complete(nid, "done",
                          f"{scored['band']} ({scored['score']}/100). "
                          f"Path: {scored['outcome']} at {scored['advance_pct']}% advance."
                          if scored["outcome"] != "declined"
                          else f"{scored['band']} ({scored['score']}/100). Below financing threshold.")
        return {}

    return node


# ---------------------------------------------------------------- node 6 ----
def compliance_kyc(ctx: PipelineContext):
    def node(_state: dict) -> dict:
        rec, nid = ctx.rec, "compliance_kyc"
        rec.node_start(nid)

        kyc_ok = ctx.msme.kyc_status == "verified"
        rec.line(nid, "res" if kyc_ok else "warn",
                 f"Exporter KYC status: {ctx.msme.kyc_status} (CKYC/DigiLocker record on file — mock source)",
                 delay=0.4)
        if not kyc_ok:
            ctx.compliance_notes.append("KYC incomplete — manual verification required before disbursal.")
            ctx.mandate_exceeded = True

        rec.line(nid, "res", "Sanctions screening: 0 hits across OFAC / UN / MAS lists (mock adapter)", delay=0.4)

        # Real exposure math against live deals in the database.
        exposure = ctx.db.execute(
            select(func.coalesce(func.sum(FinancingDeal.advance_amount), 0)).where(
                FinancingDeal.msme_id == ctx.msme.id,
                FinancingDeal.status == "financed",
            )
        ).scalar() or 0
        proposed = 0
        if ctx.scored and ctx.scored["outcome"] != "declined":
            proposed = ctx.invoice.amount * ctx.scored["advance_pct"] // 100
        rec.line(nid, "calc", f"Exposure check: live {inr(exposure)} + proposed {inr(proposed)} vs "
                              f"mandate cap {inr(config.MANDATE_MAX_EXPOSURE)}", delay=0.45)
        if exposure + proposed > config.MANDATE_MAX_EXPOSURE:
            rec.line(nid, "warn", "Proposed advance exceeds the auto-disburse mandate — routing to the "
                                  "financier desk for manual sign-off", delay=0.4)
            ctx.compliance_notes.append(
                f"Exceeds auto-disburse mandate ({inr(config.MANDATE_MAX_EXPOSURE)} live exposure cap).")
            ctx.mandate_exceeded = True

        tenor_days = max((ctx.invoice.due_on - date.today()).days, 1)
        if tenor_days > config.MANDATE_MAX_TENOR_DAYS:
            rec.line(nid, "warn", f"Tenor {tenor_days}d exceeds mandate maximum "
                                  f"{config.MANDATE_MAX_TENOR_DAYS}d", delay=0.35)
            ctx.compliance_notes.append(f"Tenor {tenor_days}d exceeds the {config.MANDATE_MAX_TENOR_DAYS}d mandate.")
            ctx.mandate_exceeded = True

        if ctx.mandate_exceeded:
            rec.node_complete(nid, "warn", "Compliance caution: outside the auto-disburse mandate — "
                                           "financier sign-off required.")
        else:
            rec.line(nid, "ok", "Within delegated mandate — eligible for auto-disbursal", delay=0.3)
            rec.node_complete(nid, "done", "Compliance clear — KYC verified, no sanctions hits, within mandate.")
        return {}

    return node


# ---------------------------------------------------------------- final -----
def finalize(ctx: PipelineContext):
    def node(state: dict) -> dict:
        rec = ctx.rec
        deal = ctx.deal
        deal.features = dict(ctx.features)

        if state.get("halted"):
            # Decision was set by the halting node (duplicate/verification declines);
            # consent halts fall through to a generic decline here.
            if deal.decision is None:
                deal.decision = {
                    "outcome": "declined",
                    "headline": "Declined — pipeline halted",
                    "banner": f"Underwriting halted: {state.get('halt_reason', 'unknown reason')}.",
                    "reasons": ["The pipeline halted before a full assessment could be made."],
                    "nextSteps": ["Resolve the issue above and request financing again."],
                }
            deal.status = "declined"
            rec.sys("Pipeline halted — remaining checks skipped.")
        else:
            scored = ctx.scored
            tenor_days = max((ctx.invoice.due_on - date.today()).days, 1)
            if scored["outcome"] == "declined":
                deal.decision = build_thin_decline(scored=scored)
                deal.status = "declined"
            else:
                extra = ctx.compliance_notes if ctx.mandate_exceeded else None
                deal.decision = build_offer_decision(
                    outcome=scored["outcome"], scored=scored, features=ctx.features,
                    invoice=ctx.invoice, buyer=ctx.buyer, tenor_days=tenor_days,
                    extra_reasons=extra,
                )
                deal.status = "manual_review" if ctx.mandate_exceeded else scored["outcome"]
                if ctx.mandate_exceeded:
                    deal.decision["manualReview"] = True
            deal.score = scored["score"]
            deal.band = scored["band"]
            deal.advance_pct = deal.decision.get("advancePct")
            deal.advance_amount = deal.decision.get("advance")
            deal.fee_amount = deal.decision.get("fee")
            deal.net_amount = deal.decision.get("net")

        deal.decided_at = now_utc()
        ctx.db.commit()
        rec.decision(deal.decision)
        rec.sys("Decision issued. Full reasoning persisted to the audit log.")
        return {}

    return node
