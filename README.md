# SpendSense

**Behavioral finance insights with explainability and consent.**

SpendSense analyzes synthetic Plaid-style transaction data to assign users to financial personas and generate personalized educational recommendations. Built for transparency: every persona assignment and recommendation includes concrete data-driven rationales. Includes operator oversight and strict consent enforcement.

**Key insight:** This is a rules-based system (no LLMs) designed for explainability, auditability, and deterministic behavior in financial contexts.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Make

### Get Running in 5 Minutes

```bash
# 1. Clone and navigate
cd SpendSense

# 2. Run automated setup (creates venv, installs all dependencies)
make setup

# 3. Activate Python virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# 4. Create environment files
cat > .env << 'EOF'
APP_ENV=dev
SEED=42
API_HOST=127.0.0.1
API_PORT=8000
DATABASE_URL=sqlite:///./data/spendsense.db
DATA_DIR=./data
PARQUET_DIR=./data/parquet
LOG_LEVEL=WARNING
DEBUG=true
FRONTEND_PORT=5173
EOF

cat > frontend/.env.local << 'EOF'
VITE_API_BASE=http://127.0.0.1:8000
EOF

# 5. Initialize database with synthetic data
python reset_and_populate.py
# This creates 50+ users with transactions, computes signals, assigns personas, generates recommendations

# 6. Start backend (Terminal 1)
make backend

# 7. Start frontend (Terminal 2 - open a new terminal window)
make frontend
```

**Now open:**
- Frontend: http://localhost:5173
- API Docs: http://127.0.0.1:8000/docs

---

## 📊 What Does It Do?

### User Flow
1. **Consent:** User opts in to data processing (required)
2. **Signal Detection:** System analyzes transactions for 30d and 180d windows
   - Subscriptions (recurring merchants, monthly spend)
   - Savings (growth rate, emergency fund)
   - Credit (utilization, interest, overdue)
   - Income (stability, cash-flow buffer)
3. **Persona Assignment:** Rules assign 1 of 5 personas based on signals
   - High Utilization (debt risk - priority 1)
   - Variable Income Budgeter
   - Subscription-Heavy
   - Savings Builder
   - Cash-Flow Optimizer
4. **Recommendations:** 3-5 educational items + 1-3 partner offers
   - Each includes plain-language rationale citing actual data
   - Example: *"Your utilization is 68%. Consider paying more than the minimum..."*
   - Mandatory educational disclaimer on all items

### Operator Flow
1. Review all users and their generated recommendations
2. Drill into signals, persona criteria, decision traces
3. Approve/reject/flag recommendations with notes
4. Full auditability of all decisions

---

## 🏗️ Project Structure

```
spendsense/
├── app/
│   ├── api/              # FastAPI routes
│   │   ├── routes_users.py
│   │   ├── routes_consent.py
│   │   ├── routes_profiles.py
│   │   ├── routes_recommendations.py
│   │   └── routes_operator.py
│   ├── core/             # Config and logging
│   ├── db/               # SQLAlchemy models, seed data
│   ├── features/         # Signal computation (credit, savings, etc.)
│   ├── personas/         # Persona rules and assignment logic
│   ├── recommend/        # Recommendation engine, content catalog
│   ├── guardrails/       # Consent, eligibility, tone checks
│   ├── schemas/          # Pydantic validation models
│   └── tests/            # Unit and integration tests
frontend/
├── src/
│   ├── pages/
│   │   ├── UserDashboard.tsx    # Customer-facing view
│   │   └── OperatorView.tsx     # Internal review dashboard
│   ├── components/              # UI components (shadcn/ui)
│   └── lib/api.ts               # API client with React Query
data/
├── spendsense.db         # SQLite database (created on first run)
└── parquet/              # Analytics files (features by window)
```

---

## 🎯 The 5 Personas (Priority Order)

Personas are **automatically assigned** using rules. First match wins.

| Priority | Persona | Trigger Criteria | Focus |
|---------|---------|------------------|-------|
| 1 | **High Utilization** | Credit ≥50% OR interest OR overdue | Reduce debt, avoid interest |
| 2 | **Variable Income Budgeter** | Pay gap >45 days AND buffer <1mo | Budgeting for irregular income |
| 3 | **Subscription-Heavy** | ≥3 subscriptions AND ≥$50/mo OR ≥10% | Audit and cancel unused services |
| 4 | **Savings Builder** | Savings +2% OR +$200/mo AND credit <30% | Goal setting, APY optimization |
| 5 | **Cash-Flow Optimizer** | Slight overspend, stable income, credit OK | Short-term budgeting tweaks |

**Why priority?** A user with high debt AND many subscriptions gets "High Utilization" (most urgent) instead of "Subscription-Heavy".

---

## 🔌 API Endpoints

Base URL: `http://127.0.0.1:8000`

### Core Endpoints
- `GET /health` - Health check
- `POST /users` - Create user
- `GET /users` - List all users

### Consent
- `POST /consent` - Record opt-in/opt-out
- `GET /consent/{user_id}/status` - Check consent status

### User Profile
- `GET /profile/{user_id}?window=30` - Get persona + signals (30d or 180d)
- Returns 403 if consent not granted

### Recommendations
- `GET /recommendations/{user_id}?window=30` - Get personalized items
- Returns 3-5 education + 1-3 offers with rationales
- Requires consent

### Operator
- `GET /operator/review?status=pending` - Review queue with pagination
- `POST /operator/recommendations/{id}/approve` - Approve/reject with notes
- `GET /operator/recommendations/{id}/reviews` - Decision trace history
- `GET /operator/fairness` - Demographic fairness analysis

### Authentication
- `POST /auth/signup` - Create new user account (user_id, email, password)
- `POST /auth/login` - Login and get JWT token
- `POST /auth/logout` - Logout (invalidates token)
- `GET /auth/me` - Get current authenticated user info

**Authentication:**
- JWT-based authentication with bcrypt password hashing
- Role-based access control: `operator` vs `card_user`
- Protected routes require `Authorization: Bearer <token>` header
- Tokens expire after 24 hours (configurable)

**Test Credentials:**
- Operator: `operator@spendsense.local` / `operator123`
- Card Users: `usr_000001` / `usr000001123` (pattern: user_id + "123")

**Full API docs:** http://127.0.0.1:8000/docs (Swagger UI)

---

## 🧪 Testing

```bash
# Run all tests
pytest -v

# Run specific test suite
pytest spendsense/app/tests/integration/test_persona_assignment.py -v

# Type checking
mypy spendsense/app

# Test coverage
pytest --cov=spendsense.app --cov-report=term-missing
```

**Test coverage:**
- **163 total tests** (36 integration + 127 unit tests)
- **Integration tests:** Full end-to-end flows including persona assignment, recommendations, consent enforcement, operator workflows, auth flows, feature pipelines
- **Unit tests:** Signal computation (credit, savings, income, subscriptions), persona rules, authentication (JWT, password hashing), fairness metrics, database models, schemas, reports
- All tests use deterministic seed (42) for reproducibility
- 20 test files covering all modules

---

## 📊 Evaluation Metrics

The system includes comprehensive automated evaluation:

```bash
# Run evaluation metrics and generate report
python run_metrics.py
```

**Generated outputs:**
- `data/eval_metrics.json` - Full metrics in JSON format
- `data/eval_metrics.csv` - Flattened metrics for spreadsheet analysis
- `data/eval_report.md` - Human-readable summary report
- `data/reports/eval_report_TIMESTAMP.md` - Historical reports

**Metrics computed:**
1. **Coverage** - % of users with persona + ≥3 behavioral signals (Target: 100%)
2. **Explainability** - % of recommendations with rationales (Target: 100%)
3. **Latency** - Time to generate recommendations per user (Target: <5s)
4. **Auditability** - % of recommendations with decision traces (Target: 100%)
5. **Fairness** - Demographic analysis across age, gender, ethnicity

**Fairness Analysis:**
- Tracks demographics: age_range, gender, ethnicity
- Detects disparities in persona assignment and recommendation distribution
- Flags groups over/under-represented by >20% threshold
- Exports per-demographic decision traces to `data/decision_traces/fairness/`

**View in Operator Dashboard:**
- Navigate to `/operator` view
- Check "Evaluation Metrics" tab for real-time fairness analysis
- Review demographic breakdowns and disparity warnings

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python API framework
- **SQLAlchemy** - ORM for SQLite
- **Pydantic** - Data validation and schemas
- **PyArrow** - Parquet files for analytics
- **structlog** - Structured logging with trace IDs
- **python-jose** - JWT token generation and validation
- **passlib (bcrypt)** - Secure password hashing
- **matplotlib** - Charts for evaluation reports (optional)

### Frontend
- **React + TypeScript** - UI framework
- **Vite** - Build tool and dev server
- **shadcn/ui** - Component library
- **Tailwind CSS** - Styling
- **React Query (TanStack Query)** - API state management

### Data Storage
- **SQLite** - Relational data (users, transactions, personas, recommendations)
- **Parquet** - Analytics (denormalized features by window)
- **JSON** - Logs and content catalog

---

## 💡 Key Design Decisions

### Why Rules-Based (No AI/LLM)?
- **Explainability:** Every decision traceable to specific rules
- **Deterministic:** Same input = same output (testable, auditable)
- **Fast:** No API calls, runs in milliseconds
- **Trustworthy:** Financial systems need predictability
- **No LLMs used:** Content is pre-written, rules are hand-coded
  - Rationale templates use f-strings with actual user data
  - No generative AI for recommendations or persona assignment
  - AI tools (Cursor/Claude) used only for code generation during development

### Why 30d and 180d Windows?
- **30d:** Recent behavior, actionable insights
- **180d:** Long-term trends, avoid false positives from one-time events

### Why Operator Approval?
- **Quality control:** Catch inappropriate or confusing recommendations
- **Legal protection:** Human oversight for financial content
- **Auditability:** Full decision trace with reviewer notes

### Why Mandatory Disclosure?
- **Legal requirement:** Not licensed financial advice
- **User trust:** Transparent about limitations
- **Risk mitigation:** Clear educational purpose

### AI Tools Used in Development
- **Cursor IDE with Claude Sonnet** - Code generation, debugging, test writing
- **No runtime AI** - System is 100% rules-based with zero LLM API calls
- **Deterministic behavior** - All randomness uses fixed seed (42) for reproducibility

---

## 📝 Development Workflow

### Using Makefile (Recommended)

```bash
make help              # Show all available commands
make setup             # First-time setup (creates venv, installs deps)
make backend           # Start FastAPI server
make frontend          # Start Vite dev server
make test              # Run pytest
make typecheck         # Run mypy
make clean             # Remove build artifacts
```

### Manual Commands (Without Make)

If you don't have Make installed, you can run commands manually:

```bash
# Initial setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Backend
uvicorn spendsense.app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (new terminal)
cd frontend && npm run dev

# Reset database and repopulate
python reset_and_populate.py

# Grant consent for testing
python grant_consent.py user_abc123
```

---

## 🎓 For New Developers

### First Time Here?

1. **Read this README** (you're doing it!)
2. **Run Quick Start** to see it working
3. **Open the frontend** and click through User Dashboard and Operator View
4. **Check API docs** at http://127.0.0.1:8000/docs
5. **Read the code:**
   - `spendsense/app/personas/rules.py` - See persona criteria
   - `spendsense/app/recommend/engine.py` - See how recommendations are generated
   - `frontend/src/pages/UserDashboard.tsx` - See user experience

### Common Tasks

**Add a new persona:**
1. Add check function to `personas/rules.py`
2. Add to `PERSONA_CHECKS` list with priority
3. Update `recommend/content_catalog.json` with tagged content
4. Add test to `tests/integration/test_persona_assignment.py`

**Add a new signal type:**
1. Create module in `features/` (e.g., `features/debt.py`)
2. Add SQLAlchemy model to `db/models.py`
3. Add Pydantic schema to `schemas/signal.py`
4. Wire into `reset_and_populate.py` pipeline
5. Update persona rules to use new signal

**Debug a recommendation:**
1. Check logs for `user_id` and `recommendation_id`
2. Look for `structlog` entries with `rationale_tone_failed` or `offer_filtered_ineligible`
3. Use `/operator/recommendations/{id}/reviews` to see decision trace

---

## 📚 Documentation

- **`PRD.md`** - Full product requirements
- **`IMPLEMENTATION_SUMMARY.md`** - What's been built
- **`TASK_LIST.md`** - Development task breakdown
- **`docs/API_TESTING.md`** - Curl examples for manual testing
- **`Peak6_SpendSense_Requirements.md`** - Original project spec

---

## ⚠️ Limitations & Known Issues

1. **Operator approval not enforced in UI** - Users see "pending" recommendations without operator approval (demo limitation, backend enforcement exists)
2. **Synthetic data only** - No real Plaid integration
3. **Single currency** - Only USD supported
4. **Frontend auth UI incomplete** - Login/Signup pages created but need integration with existing dashboard routing

---

## 🎯 Success Metrics

| Metric | Target | Current Status |
|--------|--------|----------------|
| Users with persona + ≥3 behaviors | 100% | ✅ 100% (50/50 users) |
| Recommendations with rationales | 100% | ✅ 100% (406/406 recs) |
| Latency per user | <5 seconds | ✅ 0.003s avg |
| Recommendations with decision traces | 100% | ✅ 100% (435/435 recs) |
| Test coverage | ≥10 tests | ✅ 163 tests passing |
| Fairness analysis | Required | ✅ Demographics tracked, 0 disparities |

---

## 📄 License & Disclaimer

**Educational project only. Not financial advice.**

This is a demonstration system for educational purposes. All recommendations include the disclaimer:

> *"This is educational content, not financial advice. Consult a licensed financial advisor for personalized guidance."*

Do not use this system to provide actual financial recommendations without appropriate licenses and legal review.

---

## 🤝 Contributing

This is a solo development project for learning purposes. For questions or issues, refer to the documentation in `docs/` or check the integration tests for usage examples.

---

**Built with ❤️ for explainable financial technology**

