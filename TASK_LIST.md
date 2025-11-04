## SpendSense TASK_LIST

This is a practical, beginner-friendly task list derived directly from `PRD.md`. Work top-to-bottom within each vertical slice so you can demo real value quickly. Each section explains why it exists and what to do.

---

## How to use this list (simple)
- Check off tasks as you complete them. Start with the "Vertical Slice 1" group.
- Keep code typed and validated (Pydantic + mypy). Run tests often.
- If ports are busy, update `.env` values and keep going.

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
- [x] Implement persona criteria in `spendsense/app/personas/rules.py` per PRD definitions
- [x] Implement deterministic prioritization in `spendsense/app/personas/assign.py`
- [x] Store persona per user per window (30d, 180d) with rationale in `personas` table
- [x] Handle ties and insufficient data cases
- [x] Unit tests covering all 5 personas and priority order

---

## Epic: Recommendations (education + offers)
Why: Provide clear next steps with plain-language reasons so users understand the “why”.

### Story: Recommendation engine and content
- [x] Create `spendsense/app/recommend/engine.py` (build items from persona + signals)
- [x] Add `spendsense/app/recommend/content_catalog.json` with tags mapped to personas/signals
- [x] Ensure every item has a rationale citing concrete data points
- [x] Append mandatory disclosure to every item (see PRD language)
- [x] Store items in `recommendation_items` with eligibility flags and disclosure
- [x] Unit tests for rationale formatting and duplicates handling

### Story: Eligibility and tone checks
- [x] Implement `spendsense/app/recommend/eligibility.py` (filter ineligible offers with reasons)
- [x] Implement `spendsense/app/recommend/tone.py` (no shaming, supportive, automated check)
- [x] Implement `spendsense/app/recommend/disclosure.py` (consistent disclaimer add)
- [x] Persist guardrail decisions JSON with tone/eligibility results
- [x] Unit tests for guardrail failures and edge cases

---

## Epic: Guardrails (Consent, Eligibility, Tone)
Why: Users must control their data; recommendations must be safe and respectful.

### Story: Consent enforcement
- [x] Add `spendsense/app/guardrails/consent.py` with helpers to record and check consent
- [x] Add `consent_events` table (user_id, action, timestamp, reason, by)
- [x] Middleware/hook to block processing until opt-in exists (return 403 with guidance)
- [x] Unit tests: opt-in/out flows and blocked paths

### Story: Eligibility & tone guardrails (runtime)
- [x] Add `spendsense/app/guardrails/checks.py` to centralize policy checks for offers/tone
- [x] Ensure dev-mode logs show tone rejections for debugging
- [x] Unit tests
---

## Epic: FastAPI API
Why: Expose functionality cleanly with auto docs and structured errors.

### Story: Endpoints and error handling
- [x] `POST /users` — create user
- [x] `POST /consent` — record opt-in/opt-out
- [x] `GET /profile/{user_id}` — return signals (30d/180d)
- [x] `GET /recommendations/{user_id}` — return items with rationales + disclosures
- [x] `POST /feedback` — record user feedback on items
- [x] `GET /operator/review` — operator approval queue
- [x] `POST /operator/recommendations/{id}/approve` — approve/override with notes
- [x] Structured errors via Pydantic models; consistent status codes (4xx/5xx)
- [x] structlog request IDs + decision trace IDs in logs
- [x] Integration tests for happy-path and validation failures

---

## Epic: Frontend (Vite + React + TS + shadcn/ui + Tailwind)
Why: Show users and operators what the system sees, in a simple modern UI.

### Story: Project setup
- [x] Vite + TS app scaffolding with Tailwind and shadcn/ui
- [x] API client with base URL from `VITE_API_BASE`
- [x] Feature flag for dev-only elements (e.g., decision trace)

### Story: User Dashboard
- [x] Page `frontend/src/pages/UserDashboard.tsx` lists persona (30d/180d) and signals
- [x] Render 3–5 education items and 1–3 offers with rationale and disclosure
- [x] Components: `PersonaBadge`, `DataTable`, simple cards
- [x] Basic tone-safe copy and empty-states

### Story: Operator View
- [x] Page `frontend/src/pages/OperatorView.tsx` lists users; drill into signals/persona/items
- [x] Approve/override actions with notes; flag items for follow-up
- [x] Show decision traces (dev only)
- [x] Pagination for ~100 users

---

## Epic: Evaluation & Metrics
Why: Measure coverage, explainability, latency, and simple fairness so you know it works.

### Story: Metrics harness and exports
- [x] Add `spendsense/app/eval/metrics.py` to compute metrics per PRD
- [x] Export `eval_metrics.json` and `.csv` to `./data/`
- [x] Export per-user decision traces to `./data/decision_traces/`
- [x] CLI or script to run metrics end-to-end on seeded dataset
- [x] Tests that validate targets are produced in expected format

---

## Epic: Testing & Quality
Why: Catch mistakes early and keep behavior deterministic.

- [x] Integration: seed → persona → recommendations → operator approve flow
- [x] Type checks via `mypy app` and `pytest -q` shortcuts
- [x] Optional: add `ruff`/`flake8` and simple pre-commit hooks

---

## Epic: Authentication & Authorization (Production Readiness)
Why: Move from dev demo to production app where real card users and operators can securely access the system. Implements local JWT-based auth without external dependencies.

### Story: User model and authentication backend
- [x] Add auth fields to User model: `password_hash`, `role` (card_user | operator), `is_active`
- [x] Add `spendsense/app/auth/` module with JWT token generation/validation
- [x] Add `spendsense/app/auth/password.py` for secure password hashing (bcrypt/argon2)
- [x] Add `spendsense/app/auth/dependencies.py` for FastAPI auth dependencies (get_current_user, require_role)
- [x] Store JWT secrets in `.env` (JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES)
- [ ] Unit tests for password hashing and JWT token flows

### Story: Authentication endpoints
- [x] `POST /auth/signup` — create new user with role (card_user or operator)
- [x] `POST /auth/login` — return JWT access token on valid credentials
- [x] `POST /auth/logout` — invalidate token (client-side deletion, optional backend tracking)
- [x] `GET /auth/me` — return current authenticated user info
- [x] Update `POST /users` to require operator role (create users as admin)
- [x] Add Pydantic schemas: `LoginRequest`, `SignupRequest`, `TokenResponse`, `UserAuth`
- [ ] Integration tests for signup → login → access protected endpoint

### Story: Route guards and authorization
- [x] Add `require_auth` dependency to all protected endpoints
- [x] Add `require_card_user` and `require_operator` role guards
- [x] Card users can only access their own data: `/profile/{user_id}`, `/recommendations/{user_id}` (validate user_id matches token)
- [x] Operators can access all users and operator endpoints: `/operator/*`
- [x] Update consent endpoints to use authenticated user_id from token
- [x] Return 401 Unauthorized for missing/invalid tokens, 403 Forbidden for insufficient permissions
- [ ] Integration tests for authorization scenarios (card user accessing others' data, operator access, etc.)

### Story: Frontend auth integration
- [x] Add login/signup pages: `frontend/src/pages/Login.tsx`, `frontend/src/pages/Signup.tsx`
- [x] Store JWT in localStorage/sessionStorage with secure practices
- [x] Add auth context/provider for token management and user state
- [x] Add route guards: redirect to login if not authenticated
- [x] Update API client to include `Authorization: Bearer <token>` header
- [x] Show role-specific navigation (card users see dashboard, operators see operator view)
- [x] Add logout button that clears token and redirects to login

### Story: Seed data with auth
- [x] Update `seed.py` to create default operator account (username: operator, role: operator)
- [x] Update `seed.py` to create card_user accounts for each synthetic user
- [x] Add migration script to add auth fields to existing users
- [x] Document default credentials in README for local testing

---

## Epic: Fairness & Demographic Analysis
Why: Complete PRD requirement for demographic parity checks. Ensures recommendations are fair across demographic groups.

### Story: Demographic data model
- [x] Add demographic fields to User model: `age_range` (18-24, 25-34, etc.), `gender` (optional), `ethnicity` (optional)
- [x] Make all demographic fields nullable (opt-in for privacy)
- [x] Add Pydantic schemas for demographics in `schemas/user.py`
- [x] Migration script to add demographic columns to existing users table
- [x] Update seed.py to generate realistic synthetic demographics (weighted distributions)
- [ ] Unit tests for demographic data validation

### Story: Fairness metrics computation
- [x] Add `compute_fairness_metrics()` to `spendsense/app/eval/metrics.py`
- [x] Calculate persona distribution across demographics (% of each demographic in each persona)
- [x] Calculate recommendation distribution (education vs offers) across demographics
- [x] Detect statistical disparity: flag if any demographic group is over/under-represented by >20%
- [x] Export fairness metrics to `eval_metrics.json` and `.csv`
- [x] Add fairness section to metrics summary output
- [ ] Unit tests for fairness calculations with known demographic distributions

### Story: Fairness reporting
- [x] Add fairness dashboard section to Operator View (show persona/recommendation breakdowns by demographics)
- [x] Add warnings/alerts when statistical disparity detected
- [x] Export per-demographic decision traces to `./data/decision_traces/fairness/`
- [ ] Document fairness methodology and thresholds in `docs/fairness_methodology.md`
- [ ] Integration tests for fairness calculations across full synthetic dataset

---

## Epic: Summary Report Generation
Why: Provide human-readable 1-2 page executive summaries of system performance. Makes metrics accessible to non-technical stakeholders.

### Story: Report generator module
- [x] Add `spendsense/app/eval/reports.py` with report generation logic
- [x] Support Markdown output format (simple, version-controllable)
- [x] Support PDF output format (requires `reportlab` or `weasyprint`)
- [x] Add templates for report sections: coverage, explainability, latency, auditability, fairness
- [x] Include visualizations: bar charts for persona distribution, time-series for latency
- [x] Add executive summary section with pass/fail indicators per PRD targets

### Story: Report generation CLI
- [x] Add `--report` flag to `run_metrics.py` to generate summary report
- [x] Export reports to `./data/eval_report.md` and `./data/eval_report.pdf`
- [x] Add timestamp and metadata to reports
- [x] Include sample recommendations with rationales in report
- [ ] Add comparison to previous runs (if historical metrics exist)
- [ ] Integration tests that validate report structure and completeness

### Story: Report viewing in frontend
- [x] Add "View Report" link in Operator View to display latest report
- [x] Render Markdown reports in browser (use `react-markdown` or similar)
- [x] Add download button for PDF version
- [x] Show report generation timestamp and metrics version
- [ ] Add historical reports list (if multiple reports exist)

---

## Epic: Modern UI/UX Redesign
Why: Transform from basic black-and-white to modern, startup-quality design. Improve user experience and visual appeal.

### Story: Design system and color palette
- [ ] Define color palette inspired by Tangerine (orange gradients, modern blues, clean whites)
- [ ] Primary: Orange gradient (#FF6B35 → #F7931E)
- [ ] Secondary: Deep blue (#1C3F60) and light blue (#4A90E2)
- [ ] Neutral: Modern grays (#F8F9FA, #E9ECEF, #6C757D, #343A40)
- [ ] Update Tailwind config with custom colors and gradients
- [ ] Add custom CSS variables for consistent theming
- [ ] Create design tokens file `frontend/src/styles/tokens.css`

### Story: Component redesign
- [ ] Redesign `PersonaBadge` with gradient backgrounds and icons
- [ ] Redesign `SignalCard` with visual metrics (progress bars, charts)
- [ ] Redesign `RecommendationCard` with modern card design (shadows, hover effects, gradients)
- [ ] Add micro-interactions: hover states, smooth transitions, loading animations
- [ ] Update button styles: gradient backgrounds, rounded corners, shadows
- [ ] Add icons throughout (use `lucide-react` or similar)

### Story: Dashboard layouts
- [ ] Redesign User Dashboard with hero section (gradient background, welcome message)
- [ ] Add data visualization: persona distribution pie chart, signal trend lines
- [ ] Redesign Operator View with modern table design (striped rows, hover effects)
- [ ] Add status indicators with color coding (green for approved, yellow for pending, red for rejected)
- [ ] Implement card grid layouts instead of simple lists
- [ ] Add empty states with illustrations and helpful messages

### Story: Navigation and layout
- [ ] Redesign header/navbar with gradient background
- [ ] Add user avatar/profile dropdown in navbar
- [ ] Add sidebar navigation for multi-section apps
- [ ] Implement responsive design (mobile-first approach)
- [ ] Add loading skeletons instead of plain "Loading..." text
- [ ] Add toast notifications with modern styling (success green, error red, info blue)

### Story: Login/Auth pages
- [ ] Design modern login page with split layout (illustration on left, form on right)
- [ ] Add gradient background to auth pages
- [ ] Design signup flow with progress indicator
- [ ] Add welcome/onboarding screens for new users
- [ ] Implement form validation with inline error messages
- [ ] Add "Forgot Password" flow (even if basic/local only)

### Story: Charts and data visualization
- [ ] Add Chart.js or Recharts for data visualization
- [ ] Create persona distribution donut chart
- [ ] Create signal trend line charts (30d vs 180d comparison)
- [ ] Add spending breakdown pie chart (categories from transactions)
- [ ] Visualize credit utilization with gauge charts
- [ ] Add sparklines for at-a-glance trends in cards