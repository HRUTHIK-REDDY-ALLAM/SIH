// ---------------------------------------------------------------------------
// TradeBridge AI — synthetic demo data.
// Everything below is fictional and deterministic: three invoices, each with a
// fully scripted underwriting pipeline so the live demo always plays the same.
// ---------------------------------------------------------------------------

export const APP = {
  name: 'TradeBridge AI',
  tagline: 'Export invoice financing in minutes',
  financier: 'Nexa Capital NBFC Ltd.',
}

export const COMPANY = {
  name: 'Saanvi Textiles Exports Pvt. Ltd.',
  short: 'Saanvi Textiles',
  city: 'Tiruppur, Tamil Nadu',
  gstin: '33AAFCS2841K1ZQ',
  iec: 'IEC 0416923847',
  sector: 'Organic cotton knitwear',
  bank: 'HDFC Bank ····4521',
}

export const DASH_STATS = [
  { label: 'Financed till date', value: '₹86.4L', sub: '6 invoices' },
  { label: 'Avg. decision time', value: '2m 08s', sub: 'vs 15–21 days traditional' },
  { label: 'On-time settlements', value: '100%', sub: '6 of 6 deals' },
]

export const PAST_DEALS = [
  {
    code: 'INV-2026-0139', buyer: 'Meridian Textiles Pte. Ltd.', amount: 1160000,
    status: 'Settled', detail: 'Financed 08 Jun · settled 22 Jul 2026',
  },
  {
    code: 'INV-2026-0135', buyer: 'Orchid Lane Retail Pte. Ltd.', amount: 980000,
    status: 'Settled', detail: 'Financed 19 May · settled 03 Jul 2026',
  },
  {
    code: 'INV-2026-0128', buyer: 'Meridian Textiles Pte. Ltd.', amount: 1420000,
    status: 'Settled', detail: 'Financed 28 Apr · settled 12 Jun 2026',
  },
]

// Trace-line kinds: req → outbound request · res ← data received · calc ∑ agent
// computation · ok ✓ conclusion · warn ! caution · flag ⚠ fraud alert · sys ·
const L = (d, k, text) => ({ d, k, text })

const STEP_META = {
  gather: { title: 'Data Gathering', caption: 'GST returns · bank cash-flows via Account Aggregator' },
  verify: { title: 'Invoice Verification', caption: 'Government e-invoice registry (IRN)' },
  fraud:  { title: 'Fraud & Duplicate-Financing Check', caption: 'Central lien registry · circular-trade graph' },
  buyer:  { title: 'Buyer Check', caption: 'ACRA Singapore · payment track record' },
  score:  { title: 'Risk Scoring & Pricing', caption: 'Decision · advance % · fee' },
}

const step = (id, result, finding, lines, extra = {}) => ({
  id, ...STEP_META[id], result, finding, lines, ...extra,
})

// ---------------------------------------------------------------------------
// INVOICE A — clean file, APPROVE at 80%
// ---------------------------------------------------------------------------
const invoiceA = {
  id: 'A',
  code: 'INV-2026-0142',
  buyer: { name: 'Meridian Textiles Pte. Ltd.', uen: 'UEN 199404812K', country: 'Singapore' },
  amount: 2000000,
  issued: '12 Jul 2026',
  due: '10 Sep 2026',
  tenor: '45-day tenor',
  goods: '300 cartons · organic cotton knitwear (HSN 6109)',
  irn: 'IRN a4f829…c21e',
  tag: 'Repeat buyer · 14th shipment',
  tagTone: 'blue',

  pipeline: [
    step('gather', 'done',
      'Healthy financials: ₹4.2 Cr turnover, 24/24 on-time GST filings, strong bank inflows.', [
      L(420, 'req', 'Requesting GSTR-1 / GSTR-3B summaries for GSTIN 33AAFCS2841K1ZQ (last 24 months)'),
      L(520, 'res', 'GST connected — 24 of 24 returns filed on time · reported turnover ₹4.2 Cr (FY 25-26, +18% YoY)'),
      L(400, 'req', 'Fetching 12-month bank summary via Account Aggregator (consent AA-2026-7F3K)'),
      L(520, 'res', 'Bank data received — avg monthly credits ₹38.6L · zero cheque bounces · existing EMIs regular'),
      L(340, 'calc', 'Cash-flow stability index = 0.91 (strong, seasonally adjusted)'),
    ]),
    step('verify', 'done',
      'IRN verified on the government e-invoice registry — every field matches.', [
      L(420, 'req', 'Querying NIC e-invoice registry for IRN a4f829…c21e'),
      L(500, 'res', 'IRN found — registered 12 Jul 2026 · digitally signed by GSTN'),
      L(400, 'calc', 'Matching amount ₹20,00,000 · buyer Meridian Textiles Pte. Ltd. · currency — all fields match'),
      L(260, 'ok', 'E-invoice is genuine and unaltered'),
    ]),
    step('fraud', 'done',
      'Invoice is unpledged — no duplicate financing, no circular-trade signals.', [
      L(420, 'req', 'Searching central lien registry for existing pledges on IRN a4f829…c21e'),
      L(520, 'res', 'No lien, assignment or prior financing found on this receivable'),
      L(400, 'req', 'Scanning counterparty graph (41 linked entities) for circular-trade patterns'),
      L(440, 'res', 'No circular flows · no related-party round-tripping detected'),
      L(260, 'ok', 'Clean — no duplicate financing, no fraud signals'),
    ]),
    step('buyer', 'done',
      'Buyer verified: 32-year-old Singapore company, 14/14 on-time payments to you.', [
      L(420, 'req', 'Looking up UEN 199404812K on ACRA (Singapore business registry)'),
      L(520, 'res', 'Meridian Textiles Pte. Ltd. — status Live · incorporated 1994 · paid-up capital S$2.4M'),
      L(440, 'calc', 'Relationship history: 14 prior shipments settled · buyer pays on average 1.8 days early'),
      L(260, 'ok', 'Established buyer with an excellent payment record'),
    ]),
    step('score', 'done',
      'Low risk (82/100). Approved for an 80% advance at 1.75% flat fee.', [
      L(460, 'calc', 'Scoring 23 signals across exporter health, invoice integrity, buyer strength, relationship history'),
      L(520, 'calc', 'Composite risk score = 82 / 100 → LOW RISK'),
      L(440, 'ok', 'Decision: APPROVE — advance 80% (₹16,00,000) at 1.75% flat fee'),
    ]),
  ],

  decision: {
    outcome: 'approved',
    score: 82,
    band: 'Low risk',
    headline: 'Approved — ₹16,00,000 offer ready',
    banner: 'All five checks cleared. Your financing offer is ready.',
    advancePct: 80,
    advance: 1600000,
    feePct: '1.75%',
    fee: 28000,
    net: 1572000,
    balance: 400000,
    reasons: [
      'Strong, consistent revenues — GST shows ₹4.2 Cr turnover with all 24 returns filed on time, and bank inflows comfortably cover existing obligations.',
      'The invoice is genuine — its IRN is registered with GSTN and every field matches the government e-invoice record.',
      'No double-financing — no other lender has a claim on this receivable, and no circular-trade patterns were found around it.',
      'Reliable buyer — Meridian Textiles (Singapore, est. 1994) has paid you on time 14 times in a row, averaging 1.8 days early.',
      'A 45-day tenor to a proven payer keeps the exposure short and predictable.',
    ],
    settlement: {
      payer: 'Meridian Textiles',
      payDate: '10 Sep 2026',
      tenorDays: 45,
      totalToYou: '₹19,72,000',
      allInCost: '1.4% of invoice value',
      utr: 'UTR N2072620TB84121',
    },
  },
}

// ---------------------------------------------------------------------------
// INVOICE B — duplicate financing, DECLINE (the fraud catch)
// ---------------------------------------------------------------------------
const invoiceB = {
  id: 'B',
  code: 'INV-2026-0156',
  buyer: { name: 'Straits Apparel Group Pte. Ltd.', uen: 'UEN 200806331W', country: 'Singapore' },
  amount: 3400000,
  issued: '05 Jul 2026',
  due: '25 Sep 2026',
  tenor: '60-day tenor',
  goods: '520 rolls · dyed cotton fabric (HSN 5208)',
  irn: 'IRN b7d2f4…9f4a',
  tag: 'Large order',
  tagTone: 'slate',

  pipeline: [
    step('gather', 'done',
      'Healthy financials: ₹4.2 Cr turnover, 24/24 on-time GST filings, strong bank inflows.', [
      L(420, 'req', 'Requesting GSTR-1 / GSTR-3B summaries for GSTIN 33AAFCS2841K1ZQ (last 24 months)'),
      L(520, 'res', 'GST connected — 24 of 24 returns filed on time · reported turnover ₹4.2 Cr (FY 25-26)'),
      L(400, 'req', 'Fetching 12-month bank summary via Account Aggregator (consent AA-2026-7F3K)'),
      L(500, 'res', 'Bank data received — avg monthly credits ₹38.6L · no bounces · EMIs regular'),
    ]),
    step('verify', 'done',
      'IRN is valid on the government registry and all fields match.', [
      L(420, 'req', 'Querying NIC e-invoice registry for IRN b7d2f4…9f4a'),
      L(500, 'res', 'IRN found — registered 05 Jul 2026 · digitally signed by GSTN'),
      L(380, 'calc', 'Matching amount ₹34,00,000 · buyer Straits Apparel Group Pte. Ltd. — all fields match'),
      L(260, 'ok', 'E-invoice itself is genuine'),
    ]),
    step('fraud', 'flagged',
      'DUPLICATE FINANCING — this invoice was already pledged to Apex Trade Capital on 14 Jul 2026.', [
      L(440, 'req', 'Searching central lien registry for existing pledges on IRN b7d2f4…9f4a'),
      L(700, 'warn', 'Registry returned 1 match — retrieving record…'),
      L(820, 'flag', 'ALERT — active lien found: this invoice was financed by Apex Trade Capital on 14 Jul 2026 (ref TRD-2026-88412)'),
      L(560, 'flag', 'Duplicate financing detected — the same receivable cannot back two loans'),
      L(460, 'flag', 'Declining this request · notifying the financier network · deal logged for review'),
    ], { halt: true }),
    step('buyer', 'skipped', null, []),
    step('score', 'skipped', null, []),
  ],

  decision: {
    outcome: 'declined',
    headline: 'Declined — duplicate financing detected',
    banner: 'This invoice is already financed with another lender. TradeBridge blocked it automatically.',
    evidence: {
      lender: 'Apex Trade Capital NBFC',
      financedOn: '14 Jul 2026',
      ref: 'TRD-2026-88412',
      status: 'Active lien on this receivable',
    },
    reasons: [
      'This exact invoice (IRN b7d2f4…9f4a) already carries an active lien — Apex Trade Capital financed it on 14 Jul 2026.',
      'Financing the same receivable twice means two lenders would depend on one buyer payment. That is double financing, and TradeBridge blocks it automatically.',
      'The decline is specific to this invoice. Your GST and bank profile looked healthy — any other unpledged invoice can still be financed today.',
    ],
    nextSteps: [
      'If you believe this is an error, raise a dispute quoting registry ref TRD-2026-88412 — disputes are typically resolved within 2 business days.',
      'Repeated double-pledging attempts are reported to partner financiers and credit bureaus.',
    ],
  },
}

// ---------------------------------------------------------------------------
// INVOICE C — thin file (new, unproven buyer), CONDITIONAL 50%
// ---------------------------------------------------------------------------
const invoiceC = {
  id: 'C',
  code: 'INV-2026-0161',
  buyer: { name: 'Lion City Trading Pte. Ltd.', uen: 'UEN 202502114R', country: 'Singapore' },
  amount: 850000,
  issued: '21 Jul 2026',
  due: '26 Aug 2026',
  tenor: '30-day tenor',
  goods: '120 cartons · knit t-shirts, pilot order (HSN 6109)',
  irn: 'IRN c9e13a…7b3d',
  tag: 'New buyer · first order',
  tagTone: 'amber',

  pipeline: [
    step('gather', 'done',
      'Exporter financials are healthy — but there is no payment history with this buyer to lean on.', [
      L(420, 'req', 'Requesting GSTR-1 / GSTR-3B summaries for GSTIN 33AAFCS2841K1ZQ (last 24 months)'),
      L(520, 'res', 'GST connected — 24 of 24 returns filed on time · reported turnover ₹4.2 Cr (FY 25-26)'),
      L(400, 'req', 'Fetching 12-month bank summary via Account Aggregator (consent AA-2026-7F3K)'),
      L(500, 'res', 'Bank data received — avg monthly credits ₹38.6L · no bounces'),
      L(360, 'warn', 'Note: zero receivable history with this buyer — nothing to benchmark repayment against'),
    ]),
    step('verify', 'done',
      'IRN verified on the government e-invoice registry — every field matches.', [
      L(420, 'req', 'Querying NIC e-invoice registry for IRN c9e13a…7b3d'),
      L(500, 'res', 'IRN found — registered 21 Jul 2026 · digitally signed by GSTN'),
      L(380, 'calc', 'Matching amount ₹8,50,000 · buyer Lion City Trading Pte. Ltd. — all fields match'),
      L(260, 'ok', 'E-invoice is genuine and unaltered'),
    ]),
    step('fraud', 'done',
      'Invoice is unpledged — no duplicate financing, no circular-trade signals.', [
      L(420, 'req', 'Searching central lien registry for existing pledges on IRN c9e13a…7b3d'),
      L(500, 'res', 'No lien, assignment or prior financing found'),
      L(400, 'res', 'Counterparty graph clean — no circular-trade patterns'),
      L(260, 'ok', 'No fraud signals'),
    ]),
    step('buyer', 'warn',
      'Buyer is real and active — but only 17 months old, with zero payment history with you.', [
      L(420, 'req', 'Looking up UEN 202502114R on ACRA (Singapore business registry)'),
      L(520, 'res', 'Lion City Trading Pte. Ltd. — status Live · incorporated Feb 2025 (17 months ago) · paid-up capital S$50,000'),
      L(460, 'warn', 'No payment history with this exporter · no trade references on file yet'),
      L(360, 'warn', 'Genuine company, but a thin file — treating buyer strength as unproven'),
    ]),
    step('score', 'done',
      'Moderate risk (58/100). Conditional offer: 50% advance now, or manual review for more.', [
      L(460, 'calc', 'Scoring 23 signals — exporter strong · invoice genuine · buyer unproven'),
      L(520, 'calc', 'Composite risk score = 58 / 100 → MODERATE RISK (thin buyer file)'),
      L(480, 'ok', 'Decision: CONDITIONAL — advance capped at 50% (₹4,25,000) at 2.40% flat · manual review available'),
    ]),
  ],

  decision: {
    outcome: 'conditional',
    score: 58,
    band: 'Moderate risk',
    headline: 'Conditional offer — ₹4,25,000 available now',
    banner: 'The invoice and your financials check out, but the buyer is unproven — so the advance is capped at 50%.',
    advancePct: 50,
    advance: 425000,
    feePct: '2.40%',
    fee: 10200,
    net: 414800,
    balance: 425000,
    manualReview: true,
    reasons: [
      'First transaction with this buyer — Lion City Trading has never paid you before, so there is no repayment pattern to lean on.',
      'Young counterparty — incorporated in Feb 2025 with modest paid-up capital (S$50,000). Genuine, but a limited track record.',
      'Your own financials are strong and the invoice is verified — that is why this is a conditional offer, not a decline.',
      'The advance is capped at 50% to share risk while the relationship is new. After 2–3 clean payment cycles from this buyer, the agent raises your advance rate automatically.',
    ],
    settlement: {
      payer: 'Lion City Trading',
      payDate: '26 Aug 2026',
      tenorDays: 30,
      totalToYou: '₹8,39,800',
      allInCost: '1.2% of invoice value',
      utr: 'UTR N2072620TB84177',
    },
  },
}

export const INVOICES = [invoiceA, invoiceB, invoiceC]

export const CONSENTS = [
  {
    id: 'gst',
    title: 'Share GST data',
    provider: 'GSTN, via a licensed GSP (sandbox)',
    consentId: 'GSP-2026-C-1184',
    points: [
      'GSTR-1 & GSTR-3B summaries — last 24 months',
      'Read-only · used only for this credit decision',
      'Consent valid 30 days · revocable anytime',
    ],
  },
  {
    id: 'aa',
    title: 'Share bank data via Account Aggregator',
    provider: 'RBI Account Aggregator framework (Sahamati)',
    consentId: 'AA-2026-7F3K',
    points: [
      `12-month statement summary of ${COMPANY.bank}`,
      'Fetched once, with this one-tap approval',
      'Purpose: working-capital underwriting (DEPA-compliant)',
    ],
  },
]

export const HOW_IT_WORKS = [
  { title: 'Link an invoice', text: 'Pick a confirmed export invoice to your Singapore buyer.' },
  { title: 'One-tap consent', text: 'Approve GST + bank data sharing. No paperwork, no branch visits.' },
  { title: 'AI underwrites live', text: 'Five checks — data, invoice, fraud, buyer, risk — in about 2 minutes.' },
  { title: 'Funds the same day', text: 'A licensed partner financier disburses. The loan settles itself when your buyer pays.' },
]
