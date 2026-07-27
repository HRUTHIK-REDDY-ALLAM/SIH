// Static UI copy only — all business data now comes from the backend API.

export const APP = {
  name: 'TradeBridge AI',
  tagline: 'Export invoice financing in minutes',
  financier: 'Nexa Capital NBFC Ltd.',
}

export const DEMO_ACCOUNTS = {
  msme: { email: 'demo@saanvi.in', password: 'demo1234', label: 'Exporter demo (Saanvi Textiles)' },
  financier: { email: 'fin@nexacapital.in', password: 'demo1234', label: 'Financier demo (Nexa Capital)' },
}

export const CONSENT_CARDS = [
  {
    id: 'gst',
    title: 'Share GST data',
    provider: 'GSTN, via a licensed GSP (mock adapter)',
    points: [
      'GSTR-1 & GSTR-3B summaries — last 24 months',
      'Read-only · used only for this credit decision',
      'Consent valid 30 days · revocable anytime',
    ],
  },
  {
    id: 'aa',
    title: 'Share bank data via Account Aggregator',
    provider: 'RBI Account Aggregator framework (Sahamati) — mock adapter',
    points: [
      '12-month bank statement summary',
      'Fetched once, with this one-tap approval',
      'Purpose: working-capital underwriting (DEPA-compliant)',
    ],
  },
]

export const HOW_IT_WORKS = [
  { title: 'Link an invoice', text: 'Pick a confirmed export invoice to your Singapore buyer.' },
  { title: 'One-tap consent', text: 'Approve GST + bank data sharing — stored and enforced server-side.' },
  { title: 'AI underwrites live', text: 'A six-node LangGraph pipeline runs the checks and writes every step to an audit log.' },
  { title: 'Funds the same day', text: 'A licensed partner financier disburses. The loan settles itself when your buyer pays.' },
]

// Rendered before the first poll returns; the server payload replaces it.
export const FALLBACK_STEPS = [
  { id: 'data_gathering', title: 'Data Gathering', caption: 'GST returns · bank cash-flows via Account Aggregator' },
  { id: 'invoice_verification', title: 'Invoice Verification', caption: 'Government e-invoice registry (IRN)' },
  { id: 'fraud_check', title: 'Fraud & Duplicate-Financing Check', caption: 'Central lien registry · circular-trade graph' },
  { id: 'buyer_verification', title: 'Buyer Check', caption: 'ACRA Singapore · payment track record' },
  { id: 'risk_scoring', title: 'Risk Scoring & Pricing', caption: 'Composite score · advance % · fee' },
  { id: 'compliance_kyc', title: 'Compliance & KYC', caption: 'Sanctions · exposure mandate · KYC status' },
].map((s) => ({ ...s, status: 'pending', finding: null }))
