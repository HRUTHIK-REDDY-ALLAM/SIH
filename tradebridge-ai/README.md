# TradeBridge AI

**An AI agent that turns a confirmed export invoice into working capital in ~2 minutes instead of ~3 weeks.**

Indian MSME exporters link an unpaid invoice to a Singapore buyer, tap two consents, and watch an AI agent underwrite the deal live — pulling GST + bank data, verifying the government e-invoice (IRN), checking a lien registry for duplicate financing, vetting the buyer, and pricing the risk — with its full reasoning streamed on screen. TradeBridge does **not** lend its own money: it decides, and a licensed partner financier disburses.

> ⚠️ **Prototype.** Everything runs client-side on synthetic data. No real GSTN / Account Aggregator / bank / registry connections, no credentials, no backend.

## Run it

```bash
npm install
npm run dev
```

Open the printed URL (usually http://localhost:5173). Node 18+ required.

## Demo script (for judges)

1. **Dashboard → "Request financing on an invoice."**
2. **Invoice A — INV-2026-0142, Meridian Textiles, ₹20,00,000** → approve both consents → watch the five-step live underwriting → **APPROVED**: 80% advance (₹16,00,000) at 1.75% flat, with plain-English reasons and the full reasoning trace → Accept → funds-disbursed screen with the self-settling repayment timeline.
3. **Invoice B — INV-2026-0156, Straits Apparel, ₹34,00,000** → same flow, but the **Fraud & Duplicate-Financing Check catches an active lien**: the invoice was already financed by another lender. The pipeline halts and the agent **DECLINES** with the registry record as evidence. *This is the memorable moment.*
4. **Invoice C — INV-2026-0161, Lion City Trading, ₹8,50,000** → a brand-new, 17-month-old buyer with zero payment history → **CONDITIONAL**: advance capped at 50% (₹4,25,000) with the option of manual review.
5. Optional: switch to the **Financier** tab (top right) — the same deals as the lender's deal desk sees them: risk score, evidence, mandate, full trace.

All three outcomes are **deterministic** — the demo plays the same way every time. The ↻ button in the header resets the session.

## What's real vs. simulated

| In the demo | In production |
| --- | --- |
| Scripted GST / bank findings | GSTN via a licensed GSP · RBI Account Aggregator (Sahamati) |
| Mock IRN verification | NIC e-invoice registry (IRP) lookup |
| Mock lien registry hit | TReDS-interoperable central receivables registry / CERSAI |
| Mock buyer lookup | ACRA Singapore + trade-credit bureaus |
| Templated plain-English explanations | LLM-generated explanations over the same underwriting facts |
| "Nexa Capital NBFC" partner | Licensed NBFC / bank partners disbursing under a delegated mandate |

The decision explanations are templated so the app needs no API keys; the underwriting engine (`src/useUnderwriting.js`) exposes the same facts an LLM endpoint would consume, so swapping templates for a model call is a one-file change.

## Stack

React 19 + Vite + Tailwind CSS 4 (single-page, no router, no backend). Scenario scripts live in `src/data.js`; the streaming pipeline runner in `src/useUnderwriting.js`; screens in `src/components/`.
