## 1. Project Summary

Build a SpendSense web app to transform Plaid-style transaction data into explainable behavioral insights and personalized financial education while enforcing strict consent and guardrails. MVP scope: (A) synthetic Plaid-style data ingestion and storage, (B) behavioral signal detection and persona assignment, (C) recommendations with plain-language rationales and an operator review view.

Assumptions:
- Synthetic data only (no live Plaid). Runs fully locally without external services.
- Frontend uses Vite + React + TypeScript with shadcn/ui and Tailwind CSS.
- Backend uses Python + FastAPI, SQLite (SQLAlchemy), Parquet (PyArrow), Pydantic for validation, structlog for logging, mypy for typing, pytest for tests.


## 2. Core Goals
- Users can explicitly opt into data processing and revoke consent at any time.
- Users can be assigned a clear persona (max 5) from their behavioral signals for 30d and 180d windows.
- Users can view 3–5 educational items and 1–3 partner offers with eligibility checks and a clear “because” rationale using concrete data points.
- Operators can review detected signals, personas, and recommendations, approve/override them, and see decision traces.
- The system produces evaluation metrics (coverage, explainability, latency, basic fairness) as JSON/CSV.


## 3. Non-Goals
- No real financial advice; all content is educational only.
- No live Plaid or bank connections in MVP.
- No advanced ML modeling; rules-first with simple, explainable logic.
- No production-grade auth/SSO or multitenancy; local-only demo.
- No cloud deployment; local scripts only.


## 4. Tech Stack (Solo-AI Friendly)
- Backend: FastAPI (Python) — simple, fast, auto docs; great AI familiarity.
- Data Validation: Pydantic — clear models, robust validation, easy error messages.
- Database: SQLite — zero-ops SQL; local file-backed store; perfect for demos.
- Analytics Files: Pandas + PyArrow (Parquet) — fast columnar analytics and easy local storage.
- Environment Management: Pydantic Settings — typed config from env and .env.
- Logging: structlog — structured logs for clear debugging and auditing.
- Static Types: mypy — early error detection and safer refactors.
- ORM: SQLAlchemy — mature ORM with SQLite support.
- API Docs: Auto-generated (FastAPI OpenAPI/Swagger) — zero extra work.
- Testing: pytest — simple fixtures, fast execution.
- Frontend: React + TypeScript + shadcn/ui + Tailwind CSS (Vite) — modern UI with strong DX.


## 5. Feature Breakdown — Vertical Slices

### Feature: Data Ingestion (Synthetic Plaid-Style)
- User Story: As an operator, I want to generate and ingest 50–100 synthetic users with Plaid-like schema so that I can test the full system locally without real PII.
- Acceptance Criteria:
  - Generate 50–100 users with accounts, transactions, liabilities matching schema.
  - Support CSV/JSON ingestion; validate via Pydantic models; reject invalid records with clear errors.
  - Masked identifiers; no real PII.
  - Store relational entities in SQLite; persist analytics views in Parquet.
- Data Model Notes:
  - Tables: users, accounts, transactions, liabilities, consent_events, recommendations, operator_reviews.
  - Parquet: denormalized transaction features per user per window (30d, 180d).
- Edge Cases & Errors:
  - Missing fields, negative amounts, invalid dates, unsupported currencies.
  - Business accounts filtered out via holder_category.

### Feature: Behavioral Signal Detection
- User Story: As a system, I want to compute subscriptions, savings, credit, and income stability signals over 30d and 180d so that personas can be assigned.
- Acceptance Criteria:
  - Subscriptions: recurring merchants (≥3 in 90d monthly/weekly), monthly recurring spend, subscription share of total spend.
  - Savings: net inflow to savings-like accounts, growth rate, emergency fund coverage (savings balance / avg monthly expenses).
  - Credit: utilization per card, flags for ≥30%, ≥50%, ≥80%, minimum-payment-only, interest charges present, overdue.
  - Income Stability: payroll ACH detection, frequency/variability, cash-flow buffer in months.
  - Outputs written to Parquet and queryable via API.
- Data Model Notes:
  - features.subscription_signals, features.savings_signals, features.credit_signals, features.income_signals as Parquet datasets and SQLite summaries.
- Edge Cases & Errors:
  - Sparse data, pending transactions, reversed/refunds, outliers.

### Feature: Persona Assignment (Maximum 5)
- User Story: As a user, I want to be assigned a persona that reflects my current financial behaviors so I can get relevant education.
- Acceptance Criteria:
  - Implement 4 predefined personas from requirements + 1 custom persona.
  - Deterministic priority order when multiple personas match.
  - Persona per user per window (30d, 180d) with rationale.
- Persona Definitions (from requirements):
  - Persona 1: High Utilization — Criteria: any card utilization ≥50% OR interest > 0 OR minimum-only OR overdue.
    - Focus: reduce utilization/interest; payment planning; autopay education.
  - Persona 2: Variable Income Budgeter — Criteria: median pay gap > 45 days AND cash-flow buffer < 1 month.
    - Focus: percent-based budgets; emergency fund basics; smoothing strategies.
  - Persona 3: Subscription-Heavy — Criteria: recurring merchants ≥3 AND (monthly recurring ≥ $50 in 30d OR subscription share ≥10%).
    - Focus: subscription audit; cancellation/negotiation; bill alerts.
  - Persona 4: Savings Builder — Criteria: savings growth ≥2% over window OR net savings inflow ≥$200/month AND all card utilizations < 30%.
    - Focus: goal setting; automation; APY optimization.
  - Persona 5: Cash-Flow Optimizer (Custom) — Criteria: avg monthly expenses > income by 5–15% over 30d, stable income signals present, utilization < 50%.
    - Rationale: user overspends slightly but isn’t in high-risk credit; education should target short-term cash optimization.
    - Focus: short-term budgeting tactics; expense triage; small automation wins.
- Prioritization Logic (highest to lowest): High Utilization → Variable Income Budgeter → Subscription-Heavy → Savings Builder → Cash-Flow Optimizer.
- Data Model Notes:
  - personas table storing persona_id, user_id, window, criteria_met, assigned_at.
- Edge Cases & Errors:
  - Ties resolved by priority; unknown currencies excluded; insufficient transaction history → persona = “Insufficient Data”.

### Feature: Personalization & Recommendations
- User Story: As a user, I want 3–5 educational items and 1–3 partner offers with clear reasons so I understand what to do next.
- Acceptance Criteria:
  - Each item includes a plain-language “because” that cites concrete data (e.g., utilization 68% on Visa 4523).
  - Partner offers include eligibility checks; ineligible offers are filtered out.
  - All items include mandatory disclosure: “This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.”
- Data Model Notes:
  - recommendation_items table with type {education, offer}, persona_id, rationale, eligibility_flags, disclosure.
  - Content catalog as JSON with tags mapped to personas/signals.
- Edge Cases & Errors:
  - Conflicting offers, missing eligibility data, duplicate merchants, previously shown items.

### Feature: Consent, Eligibility & Tone Guardrails
- User Story: As a user, I want control over my data and a respectful tone.
- Acceptance Criteria:
  - Consent: explicit opt-in required before any processing; per-user consent status tracked; revoke supported.
  - Eligibility: check minimum income/credit and existing accounts; block harmful products (no predatory loans).
  - Tone: enforce no shaming language; neutral and supportive phrasing; automated tone check pass.
  - Disclosure: all recommendations include educational disclaimer.
- Data Model Notes:
  - consent_events table (user_id, action, timestamp, reason, by).
  - guardrail_decisions JSON per recommendation (eligibility checks, tone check results).
- Edge Cases & Errors:
  - Revoked consent mid-run; partial eligibility data; stale tone rules.

### Feature: Operator View
- User Story: As an operator, I need to inspect signals, personas, and recommendations; approve/override with traceability.
- Acceptance Criteria:
  - List users; drill into 30d/180d signals, persona, and recommended items.
  - Approve/override actions recorded with decision trace.
  - Flag recommendations for follow-up.
- Data Model Notes:
  - operator_reviews table (recommendation_id, status, reviewer, notes, decided_at).
- Edge Cases & Errors:
  - Conflicts between multiple reviewers; pagination performance on 100 users.

### Feature: Evaluation & Metrics
- User Story: As an evaluator, I want objective metrics exported for coverage, explainability, latency, and basic fairness.
- Acceptance Criteria:
  - Metrics JSON/CSV covering: coverage (% with persona + ≥3 behaviors), explainability (% with rationales), latency per user (<5s target), fairness (simple demographic parity if demographics present).
  - Per-user decision traces exportable.
- Data Model Notes:
  - eval_metrics.json/csv, decision_traces/ per user.
- Edge Cases & Errors:
  - Missing demographics; cold-start users; performance on large synthetic sets.


## 8. .env Setup
These variables configure the app using Pydantic Settings. Create a `.env` in the repo root.

```bash
APP_ENV=dev
SEED=42
# Backend
API_HOST=127.0.0.1
API_PORT=8000
DATABASE_URL=sqlite:///./data/spendsense.db
DATA_DIR=./data
PARQUET_DIR=./data/parquet
LOG_LEVEL=INFO
DEBUG=true
# Frontend
FRONTEND_PORT=5173
```

What and why:
- APP_ENV/DEBUG/LOG_LEVEL: control behavior and verbosity (easier debugging locally).
- DATABASE_URL/DATA_DIR/PARQUET_DIR: consistent local storage locations.
- SEED: deterministic synthetic data generation and tests.
- API_HOST/API_PORT/FRONTEND_PORT: predictable local URLs.


## 9. .gitignore
Combined Node + Python for this stack.

```gitignore
# Node
node_modules/
.dist/
dist/
.vite/
coverage/
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.so
.venv/
.env
.env.*
.pytest_cache/
.mypy_cache/
# OS
.DS_Store
# Data
*.db
*.sqlite
*.sqlite3
data/**/*.parquet
logs/
# Editor
.vscode/
.idea/
```


## 10. Debugging & Logging
- Backend: Use `structlog` with JSON logs in prod-like and key-value logs in dev. Toggle via `DEBUG` and `LOG_LEVEL`. Include request ID, user_id (if present), and decision trace IDs in logs for auditing. FastAPI exception handlers return structured error responses validated with Pydantic.
- Frontend: Use browser console in dev; hide debug banners in prod build. Feature flags (e.g., show decision trace) enabled only in dev.


## 11. External Setup Instructions (Manual)
- No external services required. Ensure local tools are installed:
  - Python 3.11+
  - Node.js 18+
  - pnpm or npm (either is fine)
- If ports 8000/5173 are taken, change `API_PORT`/`FRONTEND_PORT` in `.env`.


## 12. Deployment Plan
- Local Backend
  - Create venv and install deps:
    - macOS/Linux:
      - `python -m venv .venv && source .venv/bin/activate`
    - Windows (PowerShell):
      - `python -m venv .venv; .venv\\Scripts\\Activate.ps1`
    - `pip install -r requirements.txt`
  - Run API:
    - `uvicorn app.main:app --reload --host $API_HOST --port $API_PORT`
  - API docs available at `/docs` and `/redoc`.

- Local Frontend (Vite + React + TS)
  - `npm install`
  - `npm run dev` (opens on `http://localhost:$FRONTEND_PORT`)
  - Configure API base URL via `.env` (e.g., `VITE_API_BASE=http://127.0.0.1:8000`).

- Testing & Type Checking
  - Backend tests: `pytest -q`
  - Type check: `mypy app`
  - Linting (optional): e.g., `ruff`/`flake8` if added later.


## API Design (FastAPI)
Base URL: `http://$API_HOST:$API_PORT`

Endpoints:
- POST `/users` — Create user
- POST `/consent` — Record consent (opt-in/opt-out)
- GET `/profile/{user_id}` — Behavioral profile (signals for 30d/180d)
- GET `/recommendations/{user_id}` — Recommendations with rationales and disclosures
- POST `/feedback` — Record user feedback on items
- GET `/operator/review` — Operator approval queue
- POST `/operator/recommendations/{id}/approve` — Approve/override with notes

Schemas (Pydantic models):
- User, Account, Transaction, Liability, ConsentEvent, SignalSummary, PersonaAssignment, RecommendationItem, OperatorReview, ApiError.

Status & Errors:
- 200 happy path, 4xx validation/eligibility/consent errors, 5xx unexpected; all error payloads validated and logged (structlog).


## Data Storage
- SQLite (SQLAlchemy): normalized entities and decisions.
- Parquet (PyArrow): feature tables by window for fast analytics and evaluation.
- JSON logs/exports: metrics and decision traces under `./data/`.


## Directory Structure
```
spendsense/
  app/
    main.py
    api/
      routes_users.py
      routes_profiles.py
      routes_recommendations.py
      routes_operator.py
    core/
      config.py  # Pydantic Settings
      logging.py # structlog setup
    db/
      models.py  # SQLAlchemy models
      session.py # engine/session
      seed.py    # synthetic data generator
    features/
      subscriptions.py
      savings.py
      credit.py
      income.py
    personas/
      assign.py
      rules.py
    recommend/
      engine.py
      content_catalog.json
      eligibility.py
      tone.py
      disclosure.py
    guardrails/
      consent.py
      checks.py
    eval/
      metrics.py
      traces.py
    schemas/
      user.py, account.py, transaction.py, ...
    tests/
      unit/
      integration/
  frontend/
    index.html
    src/
      main.tsx
      App.tsx
      pages/
        OperatorView.tsx
        UserDashboard.tsx
      components/
        DataTable.tsx
        PersonaBadge.tsx
      lib/ui/ (shadcn/ui components)
    tailwind.config.ts
    postcss.config.js
    package.json
  data/
    spendsense.db
    parquet/
  docs/
    decision-log/
```


## Testing Plan
- Integration: end-to-end persona assignment and recommendation generation for a seeded synthetic user; operator approve/override flow.
- Deterministic: fix `SEED` for synthetic data and random choices.


## Guardrails
- Consent: block processing and responses until opt-in exists; return 403 with guidance otherwise.
- Eligibility: require all mandatory fields; skip ineligible offers with reasons.
- Tone: content templates run through tone checker; disallow shaming phrases; return dev log when rejected (dev only).
- Disclosure: append disclaimer to every recommendation payload and UI render.


## Evaluation & Metrics Targets
- Coverage: 100% users with persona + ≥3 behaviors.
- Explainability: 100% recommendations with rationales.
- Latency: <5 seconds per user on laptop for end-to-end generation.
- Auditability: 100% recommendations have decision traces.


## 🧱 TASK_LIST.md STRUCTURE
Epics → Stories → Tasks
- Epic: Data Foundation
  - Story: Generate synthetic Plaid-like dataset
    - Tasks: build generator, validate via Pydantic, import to SQLite/Parquet
- Epic: Feature Engineering
  - Story: Compute 30d/180d signals
    - Tasks: subscriptions, savings, credit, income modules + tests
- Epic: Persona System
  - Story: Assign personas with priority
    - Tasks: rules, assignment, persistence, API
- Epic: Recommendations
  - Story: Education + offers with rationale
    - Tasks: content catalog, eligibility, tone, disclosure, API
- Epic: Guardrails & UX
  - Story: Consent and operator view
    - Tasks: consent endpoints, operator review UI, decision trace
- Epic: Evaluation
  - Story: Metrics export and report
    - Tasks: metrics harness, CSV/JSON export, fairness check


## 🧩 SOLO-DEV GUARDRAILS
- Single repo; no external services; all secrets in `.env`.
- Strict typing (mypy) and Pydantic validation at boundaries.
- Vertical slices: ship end-to-end features, not layers.
- Keep logging structured and deterministic.


## Notes for Beginners (why this structure works)
- Each section above exists to make development predictable and testable.
- Typed models (Pydantic + mypy) catch mistakes early and explain errors clearly.
- SQLite + Parquet keep data local, simple, and fast for analysis.
- structlog makes it easy to debug and audit “why” a recommendation happened.
- The operator view provides human oversight, which is critical for trust.

