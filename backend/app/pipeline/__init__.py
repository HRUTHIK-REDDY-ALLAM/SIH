# Node ids, display titles, and captions — shared by the graph and the API
# serializer so the frontend's step list is driven entirely by the backend.
NODE_DEFS = [
    ("data_gathering", "Data Gathering", "GST returns · bank cash-flows via Account Aggregator"),
    ("invoice_verification", "Invoice Verification", "Government e-invoice registry (IRN)"),
    ("fraud_check", "Fraud & Duplicate-Financing Check", "Central lien registry · circular-trade graph"),
    ("buyer_verification", "Buyer Check", "ACRA Singapore · payment track record"),
    ("risk_scoring", "Risk Scoring & Pricing", "Composite score · advance % · fee"),
    ("compliance_kyc", "Compliance & KYC", "Sanctions · exposure mandate · KYC status"),
]
