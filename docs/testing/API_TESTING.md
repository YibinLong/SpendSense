# API Testing Guide for SpendSense

This guide shows you how to test the SpendSense API using both curl commands and pytest.

## Prerequisites

1. Start the backend API:
```bash
cd /Users/yibin/Documents/WORKZONE/VSCODE/GAUNTLET_AI/4_Week/SpendSense
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
uvicorn spendsense.app.main:app --reload --host 127.0.0.1 --port 8000
```

2. Verify API is running:
```bash
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{"status": "healthy", "app": "SpendSense", "environment": "dev"}
```

---

## A. Manual Testing with Curl

### 1. Create a User

```bash
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "email_masked": "user***@example.com",
    "phone_masked": "***-***-1234"
  }'
```

**Expected Response** (201 Created):
```json
{
  "id": 1,
  "user_id": "test_user_001",
  "email_masked": "user***@example.com",
  "phone_masked": "***-***-1234",
  "created_at": "2025-11-03T10:30:00.123456"
}
```

### 2. Opt-in to Consent

**Before** opting in, trying to access /profile will return 403:

```bash
curl http://127.0.0.1:8000/profile/test_user_001
```

**Expected Error** (403 Forbidden):
```json
{
  "detail": {
    "error": "Consent required",
    "detail": "User test_user_001 has not provided consent for data processing",
    "consent_status": "not_found",
    "guidance": "POST /consent with action='opt_in' to continue"
  }
}
```

Now **opt-in**:

```bash
curl -X POST http://127.0.0.1:8000/consent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "action": "opt_in",
    "reason": "Using SpendSense dashboard",
    "by": "user_dashboard"
  }'
```

**Expected Response** (200 OK):
```json
{
  "success": true,
  "user_id": "test_user_001",
  "action": "opt_in",
  "message": "Consent recorded successfully. User has opt_in."
}
```

### 3. Check Consent Status

```bash
curl http://127.0.0.1:8000/consent/test_user_001/status
```

**Expected Response**:
```json
{
  "has_consent": true,
  "latest_action": "opt_in",
  "latest_timestamp": "2025-11-03T10:31:00.123456",
  "event_count": 1
}
```

### 4. Get User Profile

**Note**: This requires that you've run the data seed script and feature computation for this user first. If you're testing with a fresh user, the profile will show null signals.

```bash
curl http://127.0.0.1:8000/profile/test_user_001?window=30
```

**Expected Response** (if signals exist):
```json
{
  "user_id": "test_user_001",
  "window_days": 30,
  "persona": {
    "id": 1,
    "persona_id": "high_utilization",
    "window_days": 30,
    "criteria_met": {
      "persona": "high_utilization",
      "credit_utilization_max_pct": 68.5,
      "matched_on": ["credit_util_flag_50", "has_interest_charges"]
    },
    "assigned_at": "2025-11-03T10:00:00.123456"
  },
  "signals": {
    "subscriptions": {...},
    "savings": {...},
    "credit": {...},
    "income": {...}
  }
}
```

### 5. Get Recommendations

```bash
curl http://127.0.0.1:8000/recommendations/test_user_001?window=30
```

**Expected Response** (list of recommendations):
```json
[
  {
    "id": 1,
    "user_id": "test_user_001",
    "persona_id": "high_utilization",
    "item_type": "education",
    "title": "Credit Utilization 101: Why 30% Matters",
    "description": "Learn how credit utilization impacts...",
    "url": "https://example.com/credit-utilization-guide",
    "rationale": "Your credit utilization is 68.5%. Consider paying more than the minimum to reduce interest charges and improve your credit score.",
    "disclosure": "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.",
    "status": "pending",
    "created_at": "2025-11-03T10:35:00.123456"
  },
  ...
]
```

### 6. Submit Feedback on Recommendation

```bash
curl -X POST http://127.0.0.1:8000/recommendations/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_id": 1,
    "user_id": "test_user_001",
    "action": "helpful",
    "notes": "Great suggestion!"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Feedback recorded successfully (stub implementation)"
}
```

### 7. Operator Review Queue

```bash
curl "http://127.0.0.1:8000/operator/review?status_filter=pending&limit=20"
```

**Expected Response** (list of pending recommendations):
```json
[
  {
    "id": 1,
    "user_id": "test_user_001",
    "item_type": "education",
    "title": "Credit Utilization 101",
    "rationale": "Your credit utilization is 68.5%...",
    "status": "pending",
    ...
  },
  ...
]
```

### 8. Approve/Reject Recommendation

```bash
curl -X POST http://127.0.0.1:8000/operator/recommendations/1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "reviewer": "operator_alice",
    "notes": "Looks good, rationale is clear and cites concrete data"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Recommendation approved successfully",
  "review_id": 1
}
```

### 9. View Decision Trace

```bash
curl http://127.0.0.1:8000/operator/recommendations/1/reviews
```

**Expected Response**:
```json
[
  {
    "id": 1,
    "recommendation_id": 1,
    "status": "approved",
    "reviewer": "operator_alice",
    "notes": "Looks good, rationale is clear and cites concrete data",
    "decided_at": "2025-11-03T11:00:00.123456"
  }
]
```

### 10. Revoke Consent (Opt-out)

```bash
curl -X POST http://127.0.0.1:8000/consent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "action": "opt_out",
    "reason": "Testing consent revocation",
    "by": "user_dashboard"
  }'
```

After opt-out, trying to access /profile will return 403 again:

```bash
curl http://127.0.0.1:8000/profile/test_user_001
```

**Expected Error** (403 Forbidden):
```json
{
  "detail": {
    "error": "Consent required",
    "detail": "User test_user_001 has opted out of data processing...",
    "consent_status": "opt_out",
    "guidance": "POST /consent with action='opt_in' to continue"
  }
}
```

---

## B. Automated Testing with Pytest

### Run All Tests

From the project root:

```bash
pytest -v
```

### Run Only Integration Tests

```bash
pytest spendsense/app/tests/integration/ -v
```

### Run Specific Test File

```bash
# Persona assignment tests
pytest spendsense/app/tests/integration/test_persona_assignment.py -v

# Recommendations flow tests
pytest spendsense/app/tests/integration/test_recommendations_flow.py -v

# Consent enforcement tests
pytest spendsense/app/tests/integration/test_consent_enforcement.py -v

# Operator workflow tests
pytest spendsense/app/tests/integration/test_operator_workflow.py -v
```

### Run Specific Test

```bash
pytest spendsense/app/tests/integration/test_persona_assignment.py::test_high_utilization_persona_priority_1 -v
```

### Run with Coverage

```bash
pytest --cov=spendsense.app --cov-report=term-missing
```

### Run with Detailed Output

```bash
pytest -vv -s
```

**Flags explained:**
- `-v`: Verbose (show test names)
- `-vv`: More verbose (show full diffs)
- `-s`: Show print statements
- `--cov`: Measure code coverage
- `--cov-report=term-missing`: Show lines not covered

---

## C. Testing Workflow (End-to-End)

Here's a complete workflow to test the full system:

### Step 1: Start Backend

```bash
source .venv/bin/activate
uvicorn spendsense.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 2: Check API Health

```bash
curl http://127.0.0.1:8000/health
```

### Step 3: Check Auto-Generated API Docs

Open in browser:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Step 4: Create Test User

```bash
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo_user","email_masked":"demo***@example.com"}'
```

### Step 5: Opt-in Consent

```bash
curl -X POST http://127.0.0.1:8000/consent \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo_user","action":"opt_in","by":"user_dashboard"}'
```

### Step 6: Run Data Seed (if not already done)

```bash
python -m spendsense.app.db.seed
```

### Step 7: Compute Features (if not already done)

```bash
# This would be run by a separate script that calls feature computation
# For now, you'd need to run the feature computation code manually
```

### Step 8: Assign Persona

```python
# In a Python shell or script:
from spendsense.app.db.session import SessionLocal
from spendsense.app.personas.assign import assign_persona

session = SessionLocal()
persona = assign_persona("demo_user", 30, session)
print(f"Assigned persona: {persona.persona_id}")
session.close()
```

### Step 9: Generate Recommendations

```bash
curl http://127.0.0.1:8000/recommendations/demo_user?window=30
```

### Step 10: Review as Operator

```bash
# Get queue
curl http://127.0.0.1:8000/operator/review?status_filter=pending

# Approve first recommendation (ID 1)
curl -X POST http://127.0.0.1:8000/operator/recommendations/1/approve \
  -H "Content-Type: application/json" \
  -d '{"status":"approved","reviewer":"operator_demo","notes":"Approved for testing"}'
```

---

## D. Common Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created (e.g., user) |
| 400 | Bad Request | Invalid data format |
| 403 | Forbidden | Consent not found/revoked |
| 404 | Not Found | User/resource doesn't exist |
| 409 | Conflict | User already exists |
| 422 | Validation Error | Pydantic validation failed |
| 500 | Internal Error | Unexpected server error |

---

## E. Tips for Testing

1. **Use the Swagger UI** (`/docs`) for interactive API testing
2. **Check logs** in the console for detailed error traces
3. **Use trace_id** from error responses to debug issues
4. **Run pytest** before committing code to catch regressions
5. **Test consent flow** thoroughly - it's a critical guardrail

---

## F. Troubleshooting

### "Consent required" error

Make sure you've called `POST /consent` with `action: "opt_in"` before accessing protected endpoints.

### "User not found" error

Create the user first with `POST /users`.

### Empty recommendations

Make sure:
1. User has signals computed
2. Persona has been assigned
3. Content catalog matches persona tags

### Tests failing

1. Check that database schema is up to date
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Make sure `.env` file exists with correct settings

---

## G. Next Steps

- **Frontend Integration**: Use these endpoints in the React frontend
- **Operator Dashboard**: Build UI for `/operator/review` endpoint
- **User Dashboard**: Show persona and recommendations from `/profile` and `/recommendations`
- **Metrics Export**: Implement evaluation metrics endpoints (future epic)

