"""Deterministic composite risk score computed from real pipeline features.

Weights are hand-tuned but the inputs are genuinely computed upstream (GST
filing ratio, cash-flow stability from monthly credits, buyer age from ACRA
dates, on-time ratio from settled trade history, concentration vs bank inflows).
"""
from ..config import SCORE_APPROVE_MIN, SCORE_CONDITIONAL_MIN


def compute(features: dict) -> dict:
    gst_ratio = features.get("gst_on_time_ratio", 0.0)
    turnover_cr = features.get("turnover_cr", 0.0)
    stability = features.get("cashflow_stability", 0.0)
    invoice_ok = 1.0 if features.get("invoice_verified") else 0.0
    fraud_clean = 1.0 if features.get("fraud_clean") else 0.0
    age_months = features.get("buyer_age_months", 0)
    paid_up = features.get("buyer_paid_up_sgd", 0)
    history_n = features.get("history_n", 0)
    on_time_ratio = features.get("on_time_ratio", 0.0)
    concentration = features.get("concentration", 1.0)  # invoice ÷ avg monthly inflow

    exporter_health = 25.0 * gst_ratio * min(1.0, turnover_cr / 4.0)
    cash_flow = 15.0 * stability
    invoice_integrity = 10.0 * invoice_ok
    fraud_component = 10.0 * fraud_clean
    buyer_strength = 20.0 * (
        0.5 * min(1.0, age_months / 60.0)
        + 0.3 * min(1.0, paid_up / 500_000.0)
        + 0.2 * (on_time_ratio if history_n > 0 else 0.0)
    )
    relationship = 20.0 * min(1.0, history_n / 10.0)
    concentration_penalty = 15.0 * min(1.0, max(concentration, 0.0))

    raw = (exporter_health + cash_flow + invoice_integrity + fraud_component
           + buyer_strength + relationship - concentration_penalty)
    score = max(0, min(100, round(raw)))

    if score >= SCORE_APPROVE_MIN:
        band, outcome, advance_pct, fee_rate = "Low risk", "approved", 80, 0.0175
    elif score >= SCORE_CONDITIONAL_MIN:
        band, outcome, advance_pct, fee_rate = "Moderate risk", "conditional", 50, 0.0240
    else:
        band, outcome, advance_pct, fee_rate = "High risk", "declined", 0, 0.0

    return {
        "score": score,
        "band": band,
        "outcome": outcome,
        "advance_pct": advance_pct,
        "fee_rate": fee_rate,
        "components": {
            "exporter_health": round(exporter_health, 1),
            "cash_flow": round(cash_flow, 1),
            "invoice_integrity": round(invoice_integrity, 1),
            "fraud_clean": round(fraud_component, 1),
            "buyer_strength": round(buyer_strength, 1),
            "relationship": round(relationship, 1),
            "concentration_penalty": round(-concentration_penalty, 1),
        },
    }
