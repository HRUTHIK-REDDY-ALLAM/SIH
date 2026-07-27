"""Builds the plain-English decision record from real, computed features.

The templates interpolate actual values from the pipeline run (not canned
strings). Optionally, if ANTHROPIC_API_KEY is set and the `anthropic` package
is installed, the reasons are rewritten by Claude over the same facts — the
app never requires it and falls back to the templates on any failure.
"""
import json
import os

from ..serialize import fmt_date, inr


def _payer(buyer_name: str) -> str:
    return buyer_name.replace(" Pte. Ltd.", "")


def offer_numbers(amount: int, advance_pct: int, fee_rate: float) -> dict:
    advance = amount * advance_pct // 100
    fee = round(advance * fee_rate)
    return {
        "advancePct": advance_pct,
        "advance": advance,
        "feePct": f"{fee_rate * 100:.2f}%",
        "fee": fee,
        "net": advance - fee,
        "balance": amount - advance,
    }


def build_offer_decision(*, outcome: str, scored: dict, features: dict, invoice, buyer,
                         tenor_days: int, extra_reasons: list[str] | None = None) -> dict:
    nums = offer_numbers(invoice.amount, scored["advance_pct"], scored["fee_rate"])
    fee = nums["fee"]
    n_filings = features.get("gst_filings_total", 0)
    on_time_f = features.get("gst_filings_on_time", 0)
    avg_inflow = features.get("avg_monthly_credits", 0)
    hist_n = features.get("history_n", 0)
    age_months = features.get("buyer_age_months", 0)

    if outcome == "approved":
        headline = f"Approved — {inr(nums['advance'])} offer ready"
        banner = "All checks cleared. Your financing offer is ready."
        reasons = [
            f"Strong, consistent revenues — GST shows ₹{features.get('turnover_cr')} Cr turnover with "
            f"{on_time_f}/{n_filings} returns filed on time, and bank inflows (avg {inr(avg_inflow)}/month) "
            f"comfortably cover existing obligations.",
            "The invoice is genuine — its IRN is registered on the government e-invoice registry and every "
            "field matches the e-invoice record.",
            "No double-financing — the central lien registry shows no other claim on this receivable, and no "
            "circular-trade patterns were found around it.",
            f"Reliable buyer — {buyer.name} (Singapore, incorporated {features.get('buyer_incorporated', '—')}) "
            f"has settled {hist_n} prior shipments, paying on average {features.get('avg_days_early', 0):.1f} days early.",
            f"A {tenor_days}-day tenor to a proven payer keeps the exposure short and predictable.",
        ]
    else:  # conditional
        headline = f"Conditional offer — {inr(nums['advance'])} available now"
        banner = "The invoice and your financials check out, but the buyer is unproven — the advance is capped at 50%."
        reasons = [
            f"First transaction with this buyer — {buyer.name} has never paid you before, so there is no "
            "repayment pattern to lean on.",
            f"Young counterparty — incorporated {features.get('buyer_incorporated', '—')} "
            f"({age_months} months ago) with paid-up capital of S${features.get('buyer_paid_up_sgd', 0):,}. "
            "Genuine, but a limited track record.",
            "Your own financials are strong and the invoice is verified — that is why this is a conditional "
            "offer, not a decline.",
            f"The advance is capped at {scored['advance_pct']}% to share risk while the relationship is new. "
            "After 2–3 clean payment cycles from this buyer, the agent raises your advance rate automatically.",
        ]
    if extra_reasons:
        reasons.extend(extra_reasons)

    decision = {
        "outcome": outcome,
        "score": scored["score"],
        "band": scored["band"],
        "scoreComponents": scored["components"],
        "headline": headline,
        "banner": banner,
        **nums,
        "manualReview": outcome == "conditional",
        "reasons": _maybe_polish(reasons, features),
        "settlement": {
            "payer": _payer(buyer.name),
            "payDate": fmt_date(invoice.due_on),
            "tenorDays": tenor_days,
            "totalToYou": inr(invoice.amount - fee),
            "allInCost": f"{fee / invoice.amount * 100:.1f}% of invoice value",
            "utr": None,
        },
    }
    return decision


def build_duplicate_decline(*, lien, irn_short: str) -> dict:
    return {
        "outcome": "declined",
        "headline": "Declined — duplicate financing detected",
        "banner": "This invoice is already financed with another lender. TradeBridge blocked it automatically.",
        "evidence": {
            "lender": lien.lender,
            "financedOn": fmt_date(lien.financed_on),
            "ref": lien.ref,
            "status": "Active lien on this receivable",
        },
        "reasons": [
            f"This exact invoice ({irn_short}) already carries an active lien — {lien.lender} financed it "
            f"on {fmt_date(lien.financed_on)} (registry ref {lien.ref}).",
            "Financing the same receivable twice means two lenders would depend on one buyer payment. "
            "That is double financing, and TradeBridge blocks it automatically.",
            "The decline is specific to this invoice. Your GST and bank profile looked healthy — any other "
            "unpledged invoice can still be financed today.",
        ],
        "nextSteps": [
            f"If you believe this is an error, raise a dispute quoting registry ref {lien.ref} — disputes are "
            "typically resolved within 2 business days.",
            "Repeated double-pledging attempts are reported to partner financiers and credit bureaus.",
        ],
    }


def build_verification_decline(*, irn_short: str, problem: str) -> dict:
    return {
        "outcome": "declined",
        "headline": "Declined — invoice could not be verified",
        "banner": "The e-invoice registry check failed, so the agent cannot finance this receivable.",
        "reasons": [
            f"Verification of {irn_short} failed: {problem}.",
            "TradeBridge only finances receivables whose government e-invoice record exists and matches exactly.",
            "Correct the invoice with your buyer and regenerate the e-invoice, then request financing again.",
        ],
        "nextSteps": ["Regenerate the e-invoice on the IRP and retry the request."],
    }


def build_thin_decline(*, scored: dict) -> dict:
    return {
        "outcome": "declined",
        "headline": "Declined — risk score below financing threshold",
        "banner": f"Composite risk score {scored['score']}/100 is below the minimum for any advance.",
        "score": scored["score"],
        "band": scored["band"],
        "reasons": [
            f"The composite risk score came out at {scored['score']}/100 — under the minimum of 45 that the "
            "financing policy allows, even for a reduced advance.",
            "Build 2–3 settled shipments with this buyer, or finance an invoice to an established buyer, and "
            "the agent can revisit automatically.",
        ],
        "nextSteps": ["Retry with an invoice to a buyer you have trading history with."],
    }


def _maybe_polish(reasons: list[str], facts: dict) -> list[str]:
    """Optional: have Claude rewrite the explanation over the same facts.
    Off unless ANTHROPIC_API_KEY is set and the `anthropic` package is present."""
    if not os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("TB_DISABLE_LLM"):
        return reasons
    try:
        import anthropic  # optional dependency: pip install anthropic

        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            system="You rewrite credit-decision explanations for Indian MSME exporters. "
                   "Keep every number and fact exactly as given. Return ONLY a JSON array of strings, "
                   "one refined bullet per input bullet, plain and warm in tone.",
            messages=[{"role": "user", "content": json.dumps({"facts": facts, "bullets": reasons}, default=str)}],
        )
        if response.stop_reason == "refusal":
            return reasons
        text = next((b.text for b in response.content if b.type == "text"), "")
        polished = json.loads(text)
        if isinstance(polished, list) and len(polished) == len(reasons):
            return [str(p) for p in polished]
    except Exception:
        pass
    return reasons
