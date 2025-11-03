## SpendSense TASK_LIST

This is a practical, beginner-friendly task list derived directly from `PRD.md`. Work top-to-bottom within each vertical slice so you can demo real value quickly. Each section explains why it exists and what to do.

---

## How to use this list (simple)
- Check off tasks as you complete them. Start with the "Vertical Slice 1" group.
- Keep code typed and validated (Pydantic + mypy). Run tests often.
- If ports are busy, update `.env` values and keep going.

---

## Milestones (vertical slices)
- [ ] Vertical Slice 1: Seed data → compute signals (30d) → assign persona → show user dashboard (read-only)
- [ ] Vertical Slice 2: Recommendations with rationales and disclosures
- [ ] Vertical Slice 3: Consent guardrails and enforcement
- [ ] Vertical Slice 4: Operator review (approve/override)
- [ ] Vertical Slice 5: Evaluation metrics export (JSON/CSV)

---

## Epic: Repo Bootstrap & Developer Experience
Why: Get a clean, predictable local setup so everything runs the same way every time.

- [x] Create Python venv and install deps per PRD (`requirements.txt`)
- [x] Initialize Node project in `frontend/` and install deps
- [x] Add `.env` with keys from PRD under repo root
- [x] Add `.gitignore` from PRD and create `data/` + `data/parquet/` folders
- [x] Add `spendsense/app/core/config.py` (Pydantic Settings reads `.env`)
- [x] Add `spendsense/app/core/logging.py` (structlog dev/prod modes)
- [x] Add `Makefile` or `npm scripts` to run backend, frontend, tests quickly (optional)

---

## Epic: Data Foundation
Why: You need realistic data to test all features locally without any real PII.

### Story: Generate synthetic Plaid-like dataset
- [x] Define Pydantic schemas in `spendsense/app/schemas/` (user, account, transaction, liability, consent_event)
- [x] Implement SQLAlchemy models in `spendsense/app/db/models.py` matching schemas and PRD tables
- [x] Create DB engine/session in `spendsense/app/db/session.py` (SQLite from `DATABASE_URL`)
- [x] Implement synthetic data generator `spendsense/app/db/seed.py` (50–100 users)
- [x] Support CSV/JSON ingestion paths with validation and clear error messages
- [x] Persist normalized entities to SQLite
- [x] Write denormalized analytics-ready tables to Parquet under `data/parquet/`
- [x] Handle edge cases: missing fields, negative amounts, invalid dates, unsupported currencies, business accounts filter
- [x] Unit tests for generator + validation

---

## Epic: Feature Engineering (30d and 180d)
Why: Compute simple, explainable behavior signals that power personas and recommendations.

### Story: Subscriptions signals
- [x] Add `spendsense/app/features/subscriptions.py`
- [x] Detect recurring merchants (≥3 in 90d, monthly/weekly)
- [x] Compute monthly recurring spend and subscription share of total spend
- [x] Persist outputs to Parquet + SQLite summaries

### Story: Savings signals
- [x] Add `spendsense/app/features/savings.py`
- [x] Compute net inflow to savings-like accounts and growth rate
- [x] Emergency fund coverage = savings balance / avg monthly expenses
- [x] Persist outputs to Parquet + SQLite summaries

### Story: Credit signals
- [x] Add `spendsense/app/features/credit.py`
- [x] Compute utilization per card; flag ≥30%, ≥50%, ≥80%
- [x] Flags: minimum-payment-only, interest charges present, overdue
- [x] Persist outputs to Parquet + SQLite summaries

### Story: Income stability signals
- [x] Add `spendsense/app/features/income.py`
- [x] Detect payroll ACH, pay frequency/variability
- [x] Cash-flow buffer in months
- [x] Persist outputs to Parquet + SQLite summaries

---

## Epic: Persona System (max 5 personas)
Why: Personas simplify explaining behavior and choosing education content.

### Story: Persona rules and assignment
- [ ] Implement persona criteria in `spendsense/app/personas/rules.py` per PRD definitions
- [ ] Implement deterministic prioritization in `spendsense/app/personas/assign.py`
- [ ] Store persona per user per window (30d, 180d) with rationale in `personas` table
- [ ] Handle ties and insufficient data cases

---

## Epic: Recommendations (education + offers)
Why: Provide clear next steps with plain-language reasons so users understand the “why”.

### Story: Recommendation engine and content
- [ ] Create `spendsense/app/recommend/engine.py` (build items from persona + signals)
- [ ] Add `spendsense/app/recommend/content_catalog.json` with tags mapped to personas/signals
- [ ] Ensure every item has a rationale citing concrete data points
- [ ] Append mandatory disclosure to every item (see PRD language)
- [ ] Store items in `recommendation_items` with eligibility flags and disclosure

### Story: Eligibility and tone checks
- [ ] Implement `spendsense/app/recommend/eligibility.py` (filter ineligible offers with reasons)
- [ ] Implement `spendsense/app/recommend/tone.py` (no shaming, supportive, automated check)
- [ ] Implement `spendsense/app/recommend/disclosure.py` (consistent disclaimer add)
- [ ] Persist guardrail decisions JSON with tone/eligibility results

---

## Epic: Guardrails (Consent, Eligibility, Tone)
Why: Users must control their data; recommendations must be safe and respectful.

### Story: Consent enforcement
- [ ] Add `spendsense/app/guardrails/consent.py` with helpers to record and check consent
- [ ] Add `consent_events` table (user_id, action, timestamp, reason, by)
- [ ] Middleware/hook to block processing until opt-in exists (return 403 with guidance)
### Story: Eligibility & tone guardrails (runtime)
- [ ] Add `spendsense/app/guardrails/checks.py` to centralize policy checks for offers/tone
- [ ] Ensure dev-mode logs show tone rejections for debugging
---

## Epic: FastAPI API
Why: Expose functionality cleanly with auto docs and structured errors.

### Story: Endpoints and error handling
- [ ] `POST /users` — create user
- [ ] `POST /consent` — record opt-in/opt-out
- [ ] `GET /profile/{user_id}` — return signals (30d/180d)
- [ ] `GET /recommendations/{user_id}` — return items with rationales + disclosures
- [ ] `POST /feedback` — record user feedback on items
- [ ] `GET /operator/review` — operator approval queue
- [ ] `POST /operator/recommendations/{id}/approve` — approve/override with notes
- [ ] Structured errors via Pydantic models; consistent status codes (4xx/5xx)
- [ ] structlog request IDs + decision trace IDs in logs
- [ ] Integration tests for happy-path and validation failures

---

## Epic: Frontend (Vite + React + TS + shadcn/ui + Tailwind)
Why: Show users and operators what the system sees, in a simple modern UI.

### Story: Project setup
- [ ] Vite + TS app scaffolding with Tailwind and shadcn/ui
- [ ] API client with base URL from `VITE_API_BASE`
- [ ] Feature flag for dev-only elements (e.g., decision trace)

### Story: User Dashboard
- [ ] Page `frontend/src/pages/UserDashboard.tsx` lists persona (30d/180d) and signals
- [ ] Render 3–5 education items and 1–3 offers with rationale and disclosure
- [ ] Components: `PersonaBadge`, `DataTable`, simple cards
- [ ] Basic tone-safe copy and empty-states

### Story: Operator View
- [ ] Page `frontend/src/pages/OperatorView.tsx` lists users; drill into signals/persona/items
- [ ] Approve/override actions with notes; flag items for follow-up
- [ ] Show decision traces (dev only)
- [ ] Pagination for ~100 users

---

## Epic: Evaluation & Metrics
Why: Measure coverage, explainability, latency, and simple fairness so you know it works.

### Story: Metrics harness and exports
- [ ] Add `spendsense/app/eval/metrics.py` to compute metrics per PRD
- [ ] Export `eval_metrics.json` and `.csv` to `./data/`
- [ ] Export per-user decision traces to `./data/decision_traces/`
- [ ] CLI or script to run metrics end-to-end on seeded dataset
- [ ] Tests that validate targets are produced in expected format

---

## Epic: Testing & Quality
Why: Catch mistakes early and keep behavior deterministic.

- [ ] Integration: seed → persona → recommendations → operator approve flow
- [ ] Type checks via `mypy app` and `pytest -q` shortcuts
- [ ] Optional: add `ruff`/`flake8` and simple pre-commit hooks

---

## Definitions of Done (DoD)
Why: Clear finish line for each piece of work.

- [ ] Code is typed, validated, and logged (structlog) with useful IDs
- [ ] Unit tests added/updated and passing; integration path verified locally
- [ ] APIs documented via FastAPI auto docs; example responses verified
- [ ] Frontend renders without console errors; copy includes disclosure text
- [ ] Data artifacts (SQLite + Parquet + metrics) land in `./data/` paths from `.env`

---

## Vertical Slice 1 – Checklist
Goal: End-to-end demo from data to persona in UI (read-only).

- [ ] Seed synthetic data (SQLite + Parquet)
- [ ] Compute 30d signals (subscriptions, savings, credit, income)
- [ ] Assign persona with rationale (30d)
- [ ] Implement `/profile/{user_id}` and `/users`
- [ ] Render User Dashboard with persona + signals (read-only)

---

## Vertical Slice 2 – Checklist
Goal: Show recommendations with plain-language rationales and disclosure.

- [ ] Content catalog + recommendation engine
- [ ] Eligibility + tone checks + disclosure enforcement
- [ ] `/recommendations/{user_id}` endpoint
- [ ] User Dashboard renders items with rationales and disclosure

---

## Vertical Slice 3 – Checklist
Goal: Enforce explicit consent across API and UI.

- [ ] Consent endpoints and `consent_events` persistence
- [ ] Middleware to block processing without opt-in (403)
- [ ] Frontend consent flow and blocked-state UX

---

## Vertical Slice 4 – Checklist
Goal: Operator can approve/override with traceability.

- [ ] Operator queue API + approve/override endpoint
- [ ] Operator view with actions, notes, and decision traces

---

## Vertical Slice 5 – Checklist
Goal: Export metrics and traces for evaluation.

- [ ] Metrics harness exports JSON/CSV
- [ ] Decision traces per user saved under `./data/decision_traces/`
- [ ] Basic fairness calc if demographics present

---

## Quick Commands (reference)
Why: Shortcuts are friendly for beginners.

- Backend (from repo root): `uvicorn app.main:app --reload --host $API_HOST --port $API_PORT`
- Frontend (from `frontend/`): `npm run dev` → `http://localhost:$FRONTEND_PORT`
- Tests: `pytest -q`; Types: `mypy app`


