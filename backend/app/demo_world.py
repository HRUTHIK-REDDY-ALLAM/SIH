"""The synthetic 'outside world' that the MOCK adapters serve.

Everything here stands in for external systems we cannot reach from a hackathon
prototype (GSTN, Account Aggregator, ACRA, sanctions lists). It is data, not
logic — the pipeline nodes still compute over it for real. Keep this file
consistent with app/seed_data.py, which seeds the internal database.
"""
from datetime import date, timedelta

TODAY = date.today()

GSTIN_SAANVI = "33AAFCS2841K1ZQ"
BANK_SAANVI = "HDFC Bank ····4521"

UEN_MERIDIAN = "199404812K"
UEN_STRAITS = "200806331W"
UEN_LION = "202502114R"
UEN_ORCHID = "201319884D"

# Full e-invoice IRNs (64-hex). Display form is derived (first 6 + last 4).
IRN_A = "a4f829d17c3b6e4d5a2f8c91b3e67d0f45a8c2e1d3b6f907c4e18b5d3f6ac21e"
IRN_B = "b7d2f4a913c8e5d26b1f9a3c7e0d4b8f2a5c9e1b3d7f0a4c8e2b6d0f4a7c9f4a"
IRN_C = "c9e13a7f2d5b8e046a9c1e3f5b7d902a4c6e8a0b2d4f6a8c0e2a4c6e8b0d7b3d"

# --- GSTN world: filings + e-invoice registry -------------------------------
GST_PROFILES = {
    GSTIN_SAANVI: {
        "legal_name": "Saanvi Textiles Exports Pvt. Ltd.",
        "turnover_cr": 4.2,
        "yoy_growth_pct": 18,
        # 24 monthly returns, all filed on time.
        "filings": [{"period": f"{y}-{m:02d}", "on_time": True}
                    for y in (2024, 2025) for m in range(1, 13)],
    },
}

IRN_REGISTRY = {
    IRN_A: {"gstin": GSTIN_SAANVI, "buyer_uen": UEN_MERIDIAN, "amount": 2_000_000,
            "registered_on": TODAY - timedelta(days=15), "signed": True},
    IRN_B: {"gstin": GSTIN_SAANVI, "buyer_uen": UEN_STRAITS, "amount": 3_400_000,
            "registered_on": TODAY - timedelta(days=22), "signed": True},
    IRN_C: {"gstin": GSTIN_SAANVI, "buyer_uen": UEN_LION, "amount": 850_000,
            "registered_on": TODAY - timedelta(days=6), "signed": True},
}

# Counterparty graph used by the circular-trade scan.
COUNTERPARTY_GRAPH = {
    GSTIN_SAANVI: {"linked_entities": 41, "circular_pairs": []},
}

# --- Account Aggregator world ----------------------------------------------
BANK_SUMMARIES = {
    BANK_SAANVI: {
        # 12 months of credits (INR). Mean ≈ ₹38.6L; stability computed for real.
        "monthly_credits": [3_520_000, 4_180_000, 3_610_000, 3_940_000, 4_260_000,
                            3_450_000, 3_720_000, 4_050_000, 3_580_000, 3_980_000,
                            4_310_000, 3_690_000],
        "bounced_cheques_12m": 0,
        "emi_status": "regular",
    },
}

# --- ACRA (Singapore business registry) world -------------------------------
ACRA_COMPANIES = {
    UEN_MERIDIAN: {"name": "Meridian Textiles Pte. Ltd.", "status": "Live",
                   "incorporated_on": date(1994, 4, 8), "paid_up_capital_sgd": 2_400_000},
    UEN_STRAITS: {"name": "Straits Apparel Group Pte. Ltd.", "status": "Live",
                  "incorporated_on": date(2008, 6, 30), "paid_up_capital_sgd": 1_800_000},
    UEN_LION: {"name": "Lion City Trading Pte. Ltd.", "status": "Live",
               "incorporated_on": date(2025, 2, 11), "paid_up_capital_sgd": 50_000},
    UEN_ORCHID: {"name": "Orchid Lane Retail Pte. Ltd.", "status": "Live",
                 "incorporated_on": date(2013, 8, 19), "paid_up_capital_sgd": 900_000},
}

# --- Sanctions world --------------------------------------------------------
SANCTIONS_LIST = ["Volkov Trade FZE", "Redline Shipping Co", "Meraki Petrochem DMCC"]
