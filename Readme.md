# TradeBridge AI

**An AI agent that turns a confirmed export invoice into working capital in ~2 minutes instead of ~3 weeks — now a real full-stack system.**

Indian MSME exporters sign in, link an unpaid invoice to a Singapore buyer, grant two data-sharing consents, and watch a **server-side LangGraph pipeline** underwrite the deal live: pulling GST + bank data, verifying the government e-invoice (IRN), checking a **real lien registry for duplicate financing**, vetting the buyer, scoring the risk, and clearing compliance — with every step persisted to an audit log. TradeBridge does **not** lend its own money: it decides, and a licensed partner financier disburses.

```
frontend/  React 19 + Vite + Tailwind 4  ──HTTP──▶  backend/  FastAPI + LangGraph + SQLAlchemy (SQLite)
           polls the deal; renders what                        runs the 6-node pipeline in a worker thread,
           the audit log recorded                              writes steps/trace/decision to the database
```

## Run it locally

Two terminals. Requires **Python 3.11+** and **Node 18+**.

**Terminal 1 — backend (API on http://localhost:8000):**
```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      # macOS/Linux: .venv/bin/pip
.venv\Scripts\python run.py                        # macOS/Linux: .venv/bin/python run.py
```
First start creates `tradebridge.db` and seeds the demo data automatically.

**Terminal 2 — frontend (http://localhost:5173):**
```bash
cd frontend
npm install
npm run dev
```

**Demo accounts** (password `demo1234` for both):
- Exporter: `demo@saanvi.in` — the main flow
- Financier: `fin@nexacapital.in` — the Financier tab has its own sign-in

Interactive API docs: http://localhost:8000/docs · Health: http://localhost:8000/api/health

## Demo script (for judges)

1. Sign in as the exporter → **Dashboard** (company profile, stats and deal history are computed from the database).
2. **Invoice A — INV-2026-0142, Meridian Textiles, ₹20,00,000** → grant both consents (real rows in the `consents` table; the API refuses to underwrite without them) → watch the six-node pipeline stream → **APPROVED** ~80% advance → Accept. Accepting **registers a lien** on the receivable in `financing_registry` and the invoice becomes non-financeable.
3. **Invoice B — INV-2026-0156, Straits Apparel, ₹34,00,000** → the Fraud & Duplicate-Financing node runs a real SQL query against the lien registry and **finds an active lien** (seeded: Apex Trade Capital, ref TRD-2026-88412) → pipeline halts → **DECLINED** with the registry row shown as evidence. *This is the moat: it genuinely catches the duplicate, it doesn't play an animation.*
4. **Invoice C — INV-2026-0161, Lion City Trading, ₹8,50,000** → buyer is 17 months old with zero rows in `trade_history` → **CONDITIONAL** 50% → tap *Request manual review* → switch to the **Financier tab**, sign in, **Approve** with a note (writes back to the deal + audit log) → back in the exporter view, open the deal from the dashboard and Accept.
5. In the Financier tab, hit **“Simulate buyer payment”** on a financed deal → repayment settles, the lien is released, the dashboard stats update.
6. The ↻ button in the header resets and reseeds the whole database.

Outcomes are deterministic because they **emerge from seeded data** (the lien row, the trade history, the buyer's incorporation date) — not from scripted outcomes.

## What's real vs. what's mocked

**Real (no mocks involved):**
- **Persistence** — SQLAlchemy models for `msmes`, `buyers`, `invoices`, `financing_deals`, `consents`, `financing_registry`, `trade_history`, `audit_log`, `users`/`tokens` (SQLite by default; set `TB_DATABASE_URL` for Postgres).
- **Duplicate-financing detection** — the fraud node queries the `financing_registry` table; accepting an offer writes a lien; repayment releases it. Finance something twice and it will catch you.
- **Agent orchestration** — a LangGraph `StateGraph` with six nodes and conditional halt edges, running server-side per deal ([backend/app/pipeline/graph.py](backend/app/pipeline/graph.py)).
- **Explainability** — every node start, trace line, finding and decision is a row in `audit_log`; the UI renders what it reads back. Decision reasons interpolate the actually-computed numbers.
- **Consent enforcement** — deal creation 403s without active consent records, and the Data Gathering node re-checks before pulling data.
- **Risk scoring** — a deterministic feature-weighted score over computed inputs (GST filing ratio, cash-flow stability σ/μ, buyer age from registry dates, on-time ratio from settled shipments, invoice-to-inflow concentration) in [backend/app/pipeline/scoring.py](backend/app/pipeline/scoring.py).
- **Auth & roles** — salted-PBKDF2 passwords, bearer tokens, `msme` vs `financier` route guards.
- **Financier write-backs** — approve/decline overrides and repayment simulation mutate the deal, registry and audit log.

**Mocked (clearly labeled `# MOCK ADAPTER` — same interface as production, swap the internals):**

| Adapter | File | Production swap |
| --- | --- | --- |
| GST profile + IRN verification | [backend/app/adapters/gstn.py](backend/app/adapters/gstn.py) | GSTN e-invoice registry (IRP) + GST returns via a licensed GSP |
| Bank summary (consent-gated) | [backend/app/adapters/account_aggregator.py](backend/app/adapters/account_aggregator.py) | RBI Account Aggregator FIU integration (Sahamati) |
| Singapore buyer lookup | [backend/app/adapters/acra.py](backend/app/adapters/acra.py) | ACRA entity search + trade-credit bureau |
| Sanctions screening | [backend/app/adapters/sanctions.py](backend/app/adapters/sanctions.py) | OFAC/UN/MAS screening vendor |
| Disbursal & repayment rails | [backend/app/adapters/settlement.py](backend/app/adapters/settlement.py) | Partner-NBFC payout API · UPI–PayNow corridor (no real money moves) |

The synthetic “outside world” those mocks serve lives in [backend/app/demo_world.py](backend/app/demo_world.py). The lien registry ([backend/app/adapters/registry.py](backend/app/adapters/registry.py)) is **not** a mock — it is the internal table that is the product's fraud moat.

**Deliberately simplified:** no real money movement; no production security hardening (KYC/AML vendor, encryption-at-rest, rate limiting — comments mark where they plug in); single-tenant, no scaling. The unauthenticated `/api/admin/reset` exists only for demo resets.

**Optional LLM explanations:** decision bullets are templated over real computed facts. If you `pip install anthropic` and set `ANTHROPIC_API_KEY`, [backend/app/pipeline/explainer.py](backend/app/pipeline/explainer.py) has Claude rewrite them at decision time; the app is fully functional without it.

## Repo map

```
backend/
  run.py                 # python run.py → uvicorn on :8000
  app/main.py            # FastAPI app, CORS, auto-seed on first start
  app/models.py          # all tables
  app/seed_data.py       # the three scenarios as DATA (lien row, trade history, buyers)
  app/pipeline/          # LangGraph graph, 6 node implementations, scoring, explainer
  app/adapters/          # registry (real) + 5 mock adapters
  app/routers/           # auth, invoices, consents, deals, financier, admin
frontend/
  src/api.js             # fetch client + token storage
  src/useUnderwriting.js # POST /deals then poll — UI renders the audit log
  src/components/        # Login, Dashboard, SelectInvoice, Consent, Underwriting,
                         # Offer, Declined, Disbursed, Financier (deal desk)
```

Environment knobs: `TB_PACING=0` makes pipeline runs instant (tests), `TB_DATABASE_URL` swaps the database, `VITE_API_URL` points the frontend at a non-default API host.
