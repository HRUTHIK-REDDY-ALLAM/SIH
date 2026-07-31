"""Deterministic composite risk score + exact feature attribution.

The scoring model is **additive**: score = Σ component_i(features). For additive
models the Shapley decomposition is exact and cheap — each component's Shapley
value equals its marginal contribution against a fixed baseline applicant:

    φ_i = component_i(x) − component_i(baseline),  Σφ_i = score(x) − score(baseline)

So the "why" behind every score is a real, auditable computation (the same
quantity SHAP would estimate by sampling, computed here in closed form because
the model is additive), not a templated sentence. The attribution ships inside
the decision record and renders as a contribution chart in both dashboards.
"""
from ..config import SCORE_APPROVE_MIN, SCORE_CONDITIONAL_MIN

# A hypothetical "neutral thin-file applicant" — the reference point every
# attribution is measured against.
BASELINE_FEATURES = {
    "gst_on_time_ratio": 0.5,
    "turnover_cr": 1.0,
    "cashflow_stability": 0.5,
    "invoice_verified": False,
    "fraud_clean": False,
    "buyer_age_months": 12,
    "buyer_paid_up_sgd": 50_000,
    "history_n": 0,
    "on_time_ratio": 0.0,
    "concentration": 0.5,
}

COMPONENT_LABELS = {
    "exporter_health": "Exporter health (GST)",
    "cash_flow": "Cash-flow stability",
    "invoice_integrity": "Invoice integrity (IRN)",
    "fraud_clean": "Fraud cleanliness",
    "buyer_strength": "Buyer strength",
    "relationship": "Relationship history",
    "concentration_penalty": "Concentration penalty",
}


def _components(f: dict) -> dict[str, float]:
    """The additive scoring model. Concentration enters as a negative term."""
    gst_ratio = f.get("gst_on_time_ratio", 0.0)
    turnover_cr = f.get("turnover_cr", 0.0)
    stability = f.get("cashflow_stability", 0.0)
    invoice_ok = 1.0 if f.get("invoice_verified") else 0.0
    fraud_clean = 1.0 if f.get("fraud_clean") else 0.0
    age_months = f.get("buyer_age_months", 0)
    paid_up = f.get("buyer_paid_up_sgd", 0)
    history_n = f.get("history_n", 0)
    on_time_ratio = f.get("on_time_ratio", 0.0)
    concentration = f.get("concentration", 1.0)

    return {
        "exporter_health": 25.0 * gst_ratio * min(1.0, turnover_cr / 4.0),
        "cash_flow": 15.0 * stability,
        "invoice_integrity": 10.0 * invoice_ok,
        "fraud_clean": 10.0 * fraud_clean,
        "buyer_strength": 20.0 * (
            0.5 * min(1.0, age_months / 60.0)
            + 0.3 * min(1.0, paid_up / 500_000.0)
            + 0.2 * (on_time_ratio if history_n > 0 else 0.0)
        ),
        "relationship": 20.0 * min(1.0, history_n / 10.0),
        "concentration_penalty": -15.0 * min(1.0, max(concentration, 0.0)),
    }


def _detail(key: str, f: dict) -> str:
    if key == "exporter_health":
        return (f"{f.get('gst_filings_on_time', '—')}/{f.get('gst_filings_total', '—')} filings on time · "
                f"₹{f.get('turnover_cr', 0)} Cr turnover")
    if key == "cash_flow":
        return f"stability index {f.get('cashflow_stability', 0):.2f} (σ/μ over 12 months)"
    if key == "invoice_integrity":
        return "IRN verified on registry" if f.get("invoice_verified") else "not verified"
    if key == "fraud_clean":
        return "no lien · fingerprint clean · no cycles" if f.get("fraud_clean") else "not cleared"
    if key == "buyer_strength":
        return (f"{f.get('buyer_age_months', 0)} months old · "
                f"S${f.get('buyer_paid_up_sgd', 0):,} paid-up")
    if key == "relationship":
        return f"{f.get('history_n', 0)} settled shipments"
    if key == "concentration_penalty":
        return f"invoice = {f.get('concentration', 0):.2f}× avg monthly inflow"
    return ""


def compute(features: dict) -> dict:
    comp_x = _components(features)
    comp_base = _components(BASELINE_FEATURES)

    raw = sum(comp_x.values())
    base_raw = sum(comp_base.values())
    score = max(0, min(100, round(raw)))

    contributions = [
        {
            "id": key,
            "label": COMPONENT_LABELS[key],
            "phi": round(comp_x[key] - comp_base[key], 1),
            "detail": _detail(key, features),
        }
        for key in comp_x
    ]
    contributions.sort(key=lambda c: -abs(c["phi"]))

    if score >= SCORE_APPROVE_MIN:
        band, outcome, advance_pct, fee_rate = "Low risk", "approved", 80, 0.0175
    elif score >= SCORE_CONDITIONAL_MIN:
        band, outcome, advance_pct, fee_rate = "Moderate risk", "conditional", 50, 0.0240
    else:
        band, outcome, advance_pct, fee_rate = "High risk", "declined", 0, 0.0

    return {
        "score": score,
        "raw": round(raw, 1),
        "band": band,
        "outcome": outcome,
        "advance_pct": advance_pct,
        "fee_rate": fee_rate,
        "components": {k: round(v, 1) for k, v in comp_x.items()},
        "attribution": {
            "method": "Exact Shapley decomposition of the additive scoring model "
                      "(closed-form; equals SHAP for additive models)",
            "baseValue": round(base_raw, 1),
            "baseLabel": "neutral thin-file applicant",
            "contributions": contributions,
        },
    }
