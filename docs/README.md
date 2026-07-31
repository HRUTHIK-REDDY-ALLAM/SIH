# VittSetu — what's real, what's mocked, and how to productionise

This document is the honest inventory. It exists so a reviewer never has to guess whether a capability is genuinely implemented or staged for a demo.

**Rule of thumb:** anything that constitutes the *decisioning layer* is real. Anything that would require credentials for live Indian or Singaporean financial infrastructure is a mock adapter behind a production-shaped interface.

---

## 1. Real — genuinely implemented, no simulation

| Capability | Implementation | Why it's real |
|---|---|---|
| **Persistence** | [`backend/app/models.py`](../backend/app/models.py) — `msmes`, `buyers`, `invoices`, `financing_deals`, `consents`, `financing_registry`, `trade_links`, `trade_history`, `audit_log`, `users` | PostgreSQL under Docker Compose (SQLite for zero-setup local runs), SQLAlchemy 2.0 ORM. All state survives restarts. |
| **Duplicate-financing registry** | [`backend/app/adapters/registry.py`](../backend/app/adapters/registry.py) | An internal table of active liens, queried by the fraud node, written on accept, released on repayment. **It actually catches duplicates** — see the test below. |
| **Hash-anchored fingerprinting** | [`backend/app/fingerprint.py`](../backend/app/fingerprint.py) | SHA-256 over the invoice's *economic identity* (seller GSTIN, buyer UEN, amount, issue date, currency) — deliberately excluding the invoice number and IRN, so re-issuing the invoice produces the same fingerprint. |
| **Circular-trade detection** | [`fraud_check` in `nodes.py`](../backend/app/pipeline/nodes.py) | Loads `trade_links` into a **networkx DiGraph**, adds the proposed deal's edge, runs `simple_cycles` (Johnson's algorithm). A deal that closes a loop is halted. |
| **Agent orchestration** | [`backend/app/pipeline/graph.py`](../backend/app/pipeline/graph.py) | A real LangGraph `StateGraph`: six nodes, conditional halt edges out of the first three, executed server-side per deal in a worker thread. |
| **Explainability / audit** | [`backend/app/audit.py`](../backend/app/audit.py) | Every node start, trace line, finding and decision is a row in `audit_log`. The UI renders what it reads back — the "live" animation *is* the database. |
| **Score attribution** | [`backend/app/pipeline/scoring.py`](../backend/app/pipeline/scoring.py) | Exact **Shapley decomposition**. The model is additive, so `φᵢ = componentᵢ(x) − componentᵢ(baseline)` is the closed-form Shapley value — the same quantity SHAP estimates by sampling. A test asserts `baseValue + Σφ ≈ score`. |
| **Regulatory grounding (RAG)** | [`backend/app/pipeline/retriever.py`](../backend/app/pipeline/retriever.py) + [`backend/app/regs/`](../backend/app/regs/) | BM25 retrieval over a curated corpus of six regulatory summaries (20 section-level passages). The compliance node cites `doc-id §section`; citations ship in the decision JSON and render in both dashboards. |
| **Consent records & enforcement** | [`routers/consents.py`](../backend/app/routers/consents.py), [`routers/deals.py`](../backend/app/routers/deals.py), `data_gathering` node | Consents are rows with scope, reference and expiry. Deal creation **403s** without them; the pipeline node re-checks independently before any data pull. |
| **Auth & roles** | [`backend/app/auth.py`](../backend/app/auth.py) | OAuth2-style bearer **JWTs** (HS256, 12h), PBKDF2-salted passwords, `msme` vs `financier` route guards, cache-backed auth-epoch revocation. |
| **Cache / session state** | [`backend/app/cache.py`](../backend/app/cache.py) | Redis when `REDIS_URL` is set (Compose wires it), transparent in-process fallback otherwise. Caches finished deal payloads; holds the auth epoch. |
| **Financier write-backs** | [`routers/financier.py`](../backend/app/routers/financier.py) | Approve/decline overrides and repayment settlement mutate the deal, the registry and the audit log. |
| **Input validation** | Pydantic models on every route | This handles money: typed bodies, `Field(gt=0)` bounds, ownership checks, status-conflict `409`s. Malformed input returns `422`, never a crash. |

---

## 2. Mocked — clearly labeled, production-shaped interface

Each of these is a module with a `# MOCK ADAPTER` header naming its production replacement. **Swapping one means changing only the inside of that module** — the pipeline calls the same function signatures.

| Adapter | File | Swap for production |
|---|---|---|
| GST profile + IRN verification | [`adapters/gstn.py`](../backend/app/adapters/gstn.py) | GSTN e-invoice registry (IRP) via a licensed GSP; GSTR-1/3B returns API |
| Account Aggregator bank pull | [`adapters/account_aggregator.py`](../backend/app/adapters/account_aggregator.py) | RBI Account Aggregator FIU integration (Sahamati). Note the interface **already requires a consent reference**, so consent enforcement survives the swap unchanged. |
| Singapore buyer verification | [`adapters/acra.py`](../backend/app/adapters/acra.py) | ACRA entity search / MyInfo Business + a trade-credit bureau |
| Sanctions screening | [`adapters/sanctions.py`](../backend/app/adapters/sanctions.py) | UN / OFAC SDN / MAS screening vendor |
| Settlement rails | [`adapters/settlement.py`](../backend/app/adapters/settlement.py) | Partner-NBFC payout API; UPI–PayNow corridor. **No real money moves.** |
| ITFS financier placement | [`adapters/itfs.py`](../backend/app/adapters/itfs.py) | GIFT City ITFS platform where a licensed financier accepts the receivable |

The synthetic "outside world" those adapters serve lives in [`backend/app/demo_world.py`](../backend/app/demo_world.py) — GST filings, the IRN registry, ACRA companies, bank statements, sanctions lists.

**The regulatory corpus** in `backend/app/regs/` is *curated prototype summaries*, not verbatim law. Each file says so in its header. For production, replace the files with authoritative text — the retriever needs no changes.

---

## 3. Deliberately not built

Per scope, these are noted rather than implemented:

- **No real money movement.** Settlement is mocked end to end.
- **No production security hardening.** No real KYC/AML vendor, no pen-testing, no encryption-at-rest configuration, no rate limiting. The `# PRODUCTION NOTE` comments in `auth.py` and `secrets.py` mark where they attach. `POST /api/admin/reset` is intentionally unauthenticated for judge-friendly demo resets and would not exist in production.
- **No multi-tenancy, load testing, or horizontal scaling.**
- **Secrets** come from environment variables via [`backend/app/secrets.py`](../backend/app/secrets.py) — but every consumer goes through the `SecretsProvider` port, so adding `AwsSecretsManagerProvider` or `VaultProvider` is a single new class.

---

## 4. Proof it works

`cd backend && .venv/Scripts/python -m pytest` — 8 tests, all passing. The two that matter most:

- **`test_resubmitted_invoice_caught_by_fingerprint_alone`** — takes the already-financed invoice, gives it a **fresh IRN** (registered on the mock IRP so verification genuinely passes), a new invoice number and a reworded goods description. The IRN lookup misses; the **fingerprint lookup catches it**. This is the hash-anchoring claim, proven rather than asserted.
- **`test_circular_trade_loop_halts_the_deal`** — adds one edge closing a loop through the deal's own parties, then runs the otherwise-clean Invoice A. The graph scan halts it. This is the circular-trading claim, proven.

Plus a 50-assertion end-to-end API suite covering all three demo scenarios, JWT revocation, role separation, consent gating, validation errors and the settlement lifecycle.

---

## 5. Where each pipeline node gets its data

```
data_gathering        → gstn.get_gst_profile()          [MOCK]
                      → account_aggregator.fetch_bank_summary()  [MOCK, consent-gated]
                      → consents table                  [REAL]
                      → trade_history table             [REAL]

invoice_verification  → gstn.verify_irn()               [MOCK]

fraud_check           → registry.find_active_lien()                 [REAL — by IRN]
                      → registry.find_active_lien_by_fingerprint()  [REAL — by SHA-256]
                      → trade_links + networkx cycle scan           [REAL]
                      → financing_deals velocity query              [REAL]

buyer_verification    → acra.lookup_company()           [MOCK]
                      → sanctions.screen()              [MOCK]
                      → trade_history aggregates        [REAL]

risk_scoring          → scoring.compute() + Shapley attribution     [REAL]

compliance_kyc        → retriever.search() over regs/  [REAL retrieval, curated corpus]
                      → exposure/tenor/FEMA math over live deals    [REAL]
```
