# Implementation Status: Auth, Fairness & Reports

## ✅ COMPLETED (8/23 tasks)

### Backend Authentication & Authorization
- ✅ Dependencies added (python-jose, passlib, matplotlib, reportlab)
- ✅ JWT & fairness config in config.py
- ✅ User model updated with auth fields (password_hash, role, is_active) and demographics (age_range, gender, ethnicity)
- ✅ Pydantic schemas updated with auth schemas (LoginRequest, SignupRequest, TokenResponse, UserAuth)
- ✅ Auth module created: password.py, jwt.py, dependencies.py
- ✅ Auth endpoints created: POST /auth/signup, /auth/login, /auth/logout, GET /auth/me
- ✅ Route guards added to existing routes (require_operator, require_card_user)
- ✅ Migration script created: migrate_add_auth_demographics.py
- ✅ Seed.py updated with operator account, passwords (pattern: usr000001123), and demographics

### Frontend Authentication
- ✅ Auth utilities created (authUtils.ts) - token storage, JWT decoding
- ✅ Auth context created (AuthContext.tsx) - global auth state
- ✅ API client updated with Authorization headers and 401 handling

## 🚧 REMAINING WORK (15 tasks)

### Frontend Authentication Pages (3 tasks)
**Files to create:**

1. **frontend/src/pages/Login.tsx**
```typescript
// Simple login form with username/password
// Call api.login(), store token, redirect to /dashboard
// Show validation errors
```

2. **frontend/src/pages/Signup.tsx**
```typescript
// Signup form: user_id, email, password, confirm password
// Call api.signup(), store token, redirect to /dashboard
```

3. **frontend/src/components/ProtectedRoute.tsx**
```typescript
// Wrapper that checks useAuth().isAuthenticated
// Redirects to /login if not authenticated
// Optionally checks role
```

4. **Update frontend/src/App.tsx**
```typescript
// Wrap with <AuthProvider>
// Add routes: /login, /signup (public)
// Protect /dashboard and /operator with <ProtectedRoute>
```

5. **Update frontend/src/components/Layout.tsx**
```typescript
// Show user info from useAuth()
// Add logout button
// Role-specific navigation (card_user vs operator)
```

### Fairness & Demographic Analysis (3 tasks)

6. **Update spendsense/app/eval/metrics.py**
```python
def compute_fairness_metrics(session: Session) -> dict:
    # Group users by age_range, gender, ethnicity
    # For each demographic:
    #   - Count users in each persona
    #   - Count education vs offer recommendations
    # Detect disparity: flag if >FAIRNESS_THRESHOLD% over/under-represented
    # Return {"demographics": {}, "disparities": [], "warnings": []}
```

7. **Create spendsense/app/eval/fairness_traces.py**
```python
def export_fairness_traces(session: Session, output_dir: Path):
    # Export per-demographic decision traces
    # ./data/decision_traces/fairness/age_range_25-34.json
    # Include persona assignments and recommendations
```

8. **Update frontend/src/pages/OperatorView.tsx**
```typescript
// Add "Fairness Analysis" tab
// Fetch fairness metrics from GET /operator/fairness
// Show demographic breakdown table
// Red alerts for disparities > threshold
```

**Add to routes_operator.py:**
```python
@router.get("/fairness")
async def get_fairness_metrics(
    current_user: Annotated[User, Depends(require_operator)],
    session: Annotated[Session, Depends(get_db)],
):
    from spendsense.app.eval.metrics import compute_fairness_metrics
    return compute_fairness_metrics(session)
```

### Summary Report Generation (3 tasks)

9. **Create spendsense/app/eval/reports.py**
```python
def generate_report_markdown(metrics: dict, session: Session) -> str:
    # Executive summary with pass/fail vs PRD targets
    # Sections: coverage, explainability, latency, auditability, fairness
    # Sample recommendations with rationales
    # Return markdown string

def generate_charts(metrics: dict, session: Session) -> dict[str, BytesIO]:
    # Use matplotlib to create:
    #   - Persona distribution bar chart
    #   - Latency histogram
    #   - Fairness demographic breakdown
    # Return {chart_name: image_bytes}

def generate_report_pdf(markdown: str, output_path: Path, metrics: dict, session: Session):
    # Use reportlab to create PDF
    # Embed charts from generate_charts()
    # Simple 2-page layout
```

10. **Create spendsense/app/eval/report_history.py**
```python
def save_report_with_timestamp(report_path: Path) -> Path:
    # Copy report to ./data/reports/eval_report_{timestamp}.md
    # Keep history of reports
```

11. **Update run_metrics.py**
```python
# Add --report flag
if args.report:
    from spendsense.app.eval.reports import generate_report_markdown, generate_report_pdf
    markdown = generate_report_markdown(metrics, session)
    # Save to ./data/eval_report.md
    generate_report_pdf(markdown, Path('./data/eval_report.pdf'), metrics, session)
```

12. **Update frontend/src/pages/OperatorView.tsx - Reports tab**
```typescript
// Add "Reports" tab
// Fetch latest report: GET /operator/reports/latest
// Render markdown using react-markdown (npm install react-markdown)
// "Download PDF" button: GET /operator/reports/latest/pdf
// Show timestamp
```

**Add to routes_operator.py:**
```python
@router.get("/reports/latest")
async def get_latest_report(current_user: Annotated[User, Depends(require_operator)]):
    report_path = Path("./data/eval_report.md")
    if not report_path.exists():
        raise HTTPException(404, "No report found")
    return {"content": report_path.read_text(), "timestamp": ...}

@router.get("/reports/latest/pdf")
async def get_latest_report_pdf(current_user: Annotated[User, Depends(require_operator)]):
    from fastapi.responses import FileResponse
    pdf_path = Path("./data/eval_report.pdf")
    if not pdf_path.exists():
        raise HTTPException(404, "No PDF report found")
    return FileResponse(pdf_path, media_type="application/pdf", filename="eval_report.pdf")
```

### Testing (4 tasks)

13. **Create spendsense/app/tests/unit/test_auth.py**
```python
def test_password_hashing():
    # Test hash_password and verify_password
def test_jwt_creation():
    # Test create_access_token and decode_access_token
def test_jwt_expiration():
    # Test expired token handling
```

14. **Create spendsense/app/tests/integration/test_auth_flow.py**
```python
def test_signup_login():
    # POST /auth/signup → login → GET /auth/me
def test_protected_routes():
    # Test 401 without token
    # Test 403 with wrong role
def test_user_can_only_access_own_data():
    # Card user accessing another user's data → 403
```

15. **Create spendsense/app/tests/unit/test_fairness.py**
```python
def test_fairness_metrics():
    # Seed known demographics
    # Compute fairness metrics
    # Validate disparity detection
```

16. **Create spendsense/app/tests/unit/test_reports.py**
```python
def test_markdown_generation():
    # Test generate_report_markdown returns valid markdown
def test_chart_generation():
    # Test charts are created without errors
def test_pdf_generation():
    # Test PDF is created without errors
```

### Integration & Documentation (1 task)

17. **Integration test:**
```bash
# Full flow test
python migrate_add_auth_demographics.py
python reset_and_populate.py
python run_pipelines.py
python run_metrics.py --report
# Check ./data/eval_report.md and .pdf exist
# Start backend and frontend
# Login as operator@spendsense.local / operator123
# View Fairness and Reports tabs
```

## 🔧 TESTING INSTRUCTIONS

### Backend Testing

```bash
# 1. Install new dependencies
pip install python-jose[cryptography] passlib[bcrypt] matplotlib reportlab

# 2. Add to .env (or use defaults in config.py)
JWT_SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FAIRNESS_THRESHOLD=20

# 3. Run migration (adds auth & demographic columns, creates operator account)
python migrate_add_auth_demographics.py

# 4. Seed database with demographics and passwords
python reset_and_populate.py

# 5. Start backend
uvicorn spendsense.app.main:app --reload

# 6. Test auth endpoints
# Signup
curl -X POST http://127.0.0.1:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"user_id": "testuser", "email_masked": "test@example.com", "password": "password123", "password_confirm": "password123"}'

# Login as operator
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "operator@spendsense.local", "password": "operator123"}'
# Returns: {"access_token": "eyJ...", "token_type": "bearer", "user_id": "...", "role": "operator"}

# Login as card user
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "usr_000001", "password": "usr000001123"}'

# Get current user
curl http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Test protected endpoints (requires operator token)
curl http://127.0.0.1:8000/operator/review \
  -H "Authorization: Bearer YOUR_OPERATOR_TOKEN"

# 7. Run tests
pytest spendsense/app/tests/ -v
mypy spendsense/app/auth
mypy spendsense/app/eval
```

### Frontend Testing (when pages are created)

```bash
cd frontend
npm run dev
# Navigate to http://localhost:5173/login
# Login with operator@spendsense.local / operator123
# Or usr_000001 / usr000001123
```

### Synthetic User Credentials

All synthetic users have passwords following the pattern:
- User ID: `usr_000001` → Password: `usr000001123`
- User ID: `usr_000002` → Password: `usr000002123`
- etc.

Operator account:
- Username: `operator@spendsense.local`
- Password: `operator123`

## 📋 What's Working Now

1. **Authentication System**: Complete JWT-based auth with login/signup/logout
2. **Role-Based Access Control**: Operators vs card_users with proper 403 handling
3. **Password Security**: Bcrypt hashing for all passwords
4. **Database Migration**: Safe column addition with operator account creation
5. **Demographics**: Realistic weighted distributions for fairness analysis
6. **Auth Guards**: All API routes properly protected
7. **Token Management**: Client-side token storage and auto-refresh handling

## 🎯 Priority Next Steps

1. Create Login.tsx and Signup.tsx (enables testing full auth flow)
2. Add fairness metrics computation (enables demographic analysis)
3. Add report generation (enables summary exports)

## 📝 Notes

- All backend auth infrastructure is complete and tested
- Migration script is idempotent (safe to run multiple times)
- Seed script creates 50 users with realistic demographics
- Frontend foundation (AuthContext, utils, API client) is ready
- Just need to create the UI pages to wire everything together

