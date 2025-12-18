# SpendSense - Interview Explanation Guide

> A simple guide to explain YOUR project in technical interviews.

---

## The 30-Second Pitch

"SpendSense is a **financial wellness app** that analyzes bank transactions to understand spending behavior. It assigns users to one of five 'personas' (like 'High Debt' or 'Savings Builder') and gives them **personalized tips** to improve their finances. Everything is **rules-based, not AI** - so every recommendation can be explained and traced back to actual data."

---

## What Problem Does It Solve?

**The Problem:** People get generic financial advice that doesn't apply to them.

**The Solution:** SpendSense looks at YOUR actual transactions and gives advice based on YOUR real behavior. If you're spending 68% of your credit limit, it tells you *that specific number* and suggests paying it down.

---

## How It Works (Simple Version)

```
User's Bank Data → Compute Signals → Assign Persona → Generate Recommendations
```

1. **Ingest Data** - Load transactions, accounts, credit cards
2. **Compute Signals** - Calculate things like credit utilization, savings rate, subscription spending
3. **Assign Persona** - Match user to one of 5 categories based on rules
4. **Generate Tips** - Pull relevant education items and explain WHY they apply

---

## The Tech Stack (What To Say)

### Backend: "Python with FastAPI"

**FastAPI** is a modern Python web framework. Think of it like Express.js but for Python.

- Why FastAPI? It's fast, has automatic API documentation, and handles validation well
- The API lives at `spendsense/app/`
- Entry point: `main.py` sets up routes and middleware

### Database: "SQLite with SQLAlchemy ORM"

**SQLAlchemy** lets you write Python classes instead of raw SQL.

```python
# Instead of: SELECT * FROM users WHERE id = 1
# You write:
user = session.query(User).filter(User.id == 1).first()
```

- Tables: users, accounts, transactions, recommendations, etc.
- Models defined in `db/models.py`

### Frontend: "React with TypeScript"

- **React** - Component-based UI library
- **TypeScript** - JavaScript with types (catches errors early)
- **Vite** - Fast build tool (like webpack but faster)
- **shadcn/ui** - Pre-built UI components (buttons, forms, etc.)
- **React Query** - Handles API calls and caching

### Authentication: "JWT Tokens"

**JWT (JSON Web Token)** is like a secure ID badge.

1. User logs in with username/password
2. Server gives them a JWT token
3. User sends token with every request
4. Server verifies token to know who they are

Passwords are hashed with **bcrypt** (one-way encryption, can't be reversed).

---

## The 5 Personas (Core Business Logic)

This is the heart of the app. Users get assigned to ONE persona based on rules:

| # | Persona | Who Gets It | What They Need |
|---|---------|-------------|----------------|
| 1 | **High Utilization** | Credit card balance > 50% of limit | Tips to pay down debt |
| 2 | **Variable Income** | Freelancers with irregular paychecks | Budgeting for inconsistent income |
| 3 | **Subscription-Heavy** | 3+ subscriptions OR $50+/month on subscriptions | Audit unused services |
| 4 | **Savings Builder** | Growing savings, low debt | Goal setting, better savings rates |
| 5 | **Cash-Flow Optimizer** | Overspending slightly, otherwise healthy | Small budget tweaks |

**Key Point:** First match wins. We check in order 1→5, and stop at the first match.

---

## The 4 Signals (What We Calculate)

Signals are numbers we compute from transaction data:

### 1. Credit Signals
- **Utilization** = Balance / Limit × 100
- Example: $680 balance on $1000 limit = 68% utilization
- Flags when > 30%, 50%, 80%

### 2. Income Signals
- How much money comes IN
- How often (weekly, bi-weekly, monthly)
- Is it stable or irregular?

### 3. Savings Signals
- Is savings account growing?
- How many months of expenses saved (buffer)?

### 4. Subscription Signals
- How many recurring charges?
- Total subscription spending per month
- What % of total spending is subscriptions?

---

## API Endpoints (The Routes)

When someone asks "how does the frontend talk to the backend?":

```
POST /auth/login        → Get JWT token
GET  /profile/{user_id} → Get persona + signals
GET  /recommendations/{user_id} → Get personalized tips
POST /consent           → Record user opt-in
GET  /operator/review   → Operator sees pending recommendations
```

The frontend calls these using **fetch** (or React Query).

---

## How Recommendations Work

1. **Look up persona** - User is "High Utilization"
2. **Filter content catalog** - Get tips tagged for that persona
3. **Build rationale** - "Your utilization is 68% on your Visa. Paying $200 would drop it below 50%."
4. **Add disclosure** - Legal text saying "this is education, not financial advice"
5. **Store in database** - Operator can review before user sees it

**Key Point:** The rationale cites REAL numbers from their data. Not generic advice.

---

## Why Rules-Based? (Not AI/ML)

This is a great interview talking point:

"We chose rules-based logic instead of ML because:
1. **Explainability** - Every decision traces to specific code
2. **Deterministic** - Same input = same output (testable)
3. **Compliance** - Financial regulators want transparency
4. **Speed** - No API calls, millisecond response times
5. **Auditability** - Full trace of why each recommendation was made"

---

## The Operator Flow

There's a human-in-the-loop for quality control:

1. System generates recommendations
2. Recommendations start as "pending"
3. Operator reviews and approves/rejects
4. Only approved recommendations show to users

This is for **legal protection** and **quality control**.

---

## Testing (What To Say)

"We have 163 tests covering the core business logic."

- **Unit tests** - Test individual functions (like credit calculation)
- **Integration tests** - Test full flows (like persona assignment end-to-end)
- Run with: `pytest -v`

Example test: "If credit utilization is 68%, user should get High Utilization persona"

---

## Project Structure (Where Things Live)

```
SpendSense/
├── spendsense/app/          # Backend Python code
│   ├── api/                 # API routes (endpoints)
│   ├── auth/                # Login/JWT logic
│   ├── db/                  # Database models
│   ├── features/            # Signal calculations
│   ├── personas/            # Persona assignment rules
│   ├── recommend/           # Recommendation engine
│   └── tests/               # All tests
├── frontend/                # React app
│   ├── src/pages/           # Main pages
│   ├── src/components/      # UI components
│   └── src/lib/             # API calls
└── data/                    # Database + sample data
```

---

## Key Files to Know

If interviewer asks "show me the code for X":

| What | File |
|------|------|
| Persona rules | `spendsense/app/personas/rules.py` |
| Credit calculation | `spendsense/app/features/credit.py` |
| Recommendation logic | `spendsense/app/recommend/engine.py` |
| Database models | `spendsense/app/db/models.py` |
| Main API setup | `spendsense/app/main.py` |
| Frontend dashboard | `frontend/src/pages/UserDashboard.tsx` |

---

## Common Interview Questions

### "Walk me through the architecture"

"It's a **three-tier architecture**:
1. **Frontend** - React app that users interact with
2. **Backend** - FastAPI server that handles business logic
3. **Database** - SQLite storing users, transactions, recommendations

Frontend makes HTTP requests to backend, backend queries database and returns JSON."

### "How do you handle authentication?"

"JWT tokens. User logs in with email/password, we verify password hash with bcrypt, generate a JWT token valid for 24 hours, and client sends that token in the Authorization header for all protected routes."

### "Why not use machine learning?"

"Financial recommendations need to be explainable. If a regulator asks 'why did you recommend this?', we can point to exact rules. ML is a black box. Plus it's faster and more testable with deterministic rules."

### "How do you ensure fairness?"

"We track recommendations across demographics (age, gender, etc.) and flag if any group gets significantly different treatment. It's automated - runs as part of our evaluation metrics."

### "How do you test this?"

"163 automated tests covering unit and integration scenarios. Unit tests check individual functions. Integration tests check full flows like 'user with X data gets Y persona'. We also do type checking with MyPy and linting with Ruff."

---

## Buzzwords to Use Naturally

- **REST API** - The backend follows REST conventions
- **ORM** - SQLAlchemy is our Object-Relational Mapper
- **JWT** - JSON Web Tokens for authentication
- **Pydantic** - Data validation library (ensures API inputs are valid)
- **CORS** - Cross-Origin Resource Sharing (lets frontend talk to backend)
- **Middleware** - Code that runs on every request (like logging)
- **Deterministic** - Same input always gives same output
- **Auditability** - Can trace every decision

---

## What Makes This Project Good

1. **Real business value** - Solves an actual problem
2. **Full stack** - Frontend + Backend + Database
3. **Production patterns** - Auth, testing, error handling, logging
4. **Thoughtful design** - Rules-based for explainability
5. **Clean code** - Type hints, tests, linting

---

## Quick Commands

```bash
# Run backend
make backend

# Run frontend
make frontend

# Run tests
pytest -v

# Check types
mypy spendsense/app

# See API docs
# Open http://127.0.0.1:8000/docs
```

---

## Final Tip

Don't memorize everything. Focus on:
1. What the app DOES (financial wellness + personalization)
2. WHY key decisions were made (rules-based for explainability)
3. HOW the main flow works (data → signals → persona → recommendations)

If you don't know something, say "I'd need to look at the code to give you the exact implementation, but conceptually it works like..."

Good luck!
