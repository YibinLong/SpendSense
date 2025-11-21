# SpendSense Setup Instructions

## Quick Start

This guide shows you exactly how to get SpendSense running on your machine.

---

## Prerequisites

- **Python 3.11+** installed
- **Node.js 18+** installed
- **Terminal/Command Prompt** access

---

## Step 1: Create Required Environment Files

### 1.1 Create `.env` in project root

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

**Why this is needed:**
- The backend reads configuration from this file using Pydantic Settings
- Without it, the app won't know where to find the database or what port to use

### 1.2 Create `frontend/.env.local`

```bash
VITE_API_BASE=http://127.0.0.1:8000
```

**Why this is needed:**
- The frontend needs to know where the backend API is running
- Vite automatically loads this file in development mode

---

## Step 2: Backend Setup

### Option A: Using Makefile (Recommended)

```bash
# Create virtual environment
make venv

# Activate it (macOS/Linux)
source .venv/bin/activate

# Install dependencies
make install
```

### Option B: Manual Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**What happens here:**
- Creates an isolated Python environment in `.venv/` folder
- Installs FastAPI, Pydantic, structlog, and other dependencies
- Keeps your system Python clean

---

## Step 3: Frontend Setup

### Option A: Using Makefile

```bash
make frontend-install
```

### Option B: Manual Setup

```bash
cd frontend
npm install
cd ..
```

**What happens here:**
- Installs React, Vite, TypeScript, Tailwind CSS, and other frontend dependencies
- Creates `node_modules/` folder with all packages

---

## Step 4: Test the Backend

### Start the backend server

```bash
# Using Makefile
make backend

# OR manually
uvicorn spendsense.app.main:app --reload --host 127.0.0.1 --port 8000
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/SpendSense']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Test the endpoints

1. **Health Check:**
   - Open browser: http://127.0.0.1:8000/health
   - Should see: `{"status":"healthy","app":"SpendSense","environment":"dev"}`

2. **API Documentation:**
   - Open browser: http://127.0.0.1:8000/docs
   - Should see interactive Swagger UI with available endpoints

3. **Root Endpoint:**
   - Open browser: http://127.0.0.1:8000/
   - Should see welcome message with links

**What this confirms:**
- ✅ Backend is running
- ✅ FastAPI is working
- ✅ Configuration is loaded correctly
- ✅ Logging is configured

---

## Step 5: Test the Frontend

**In a NEW terminal window:**

```bash
# Using Makefile
make frontend

# OR manually
cd frontend
npm run dev
```

**Expected output:**
```
  VITE v7.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### Visit the frontend

- Open browser: http://localhost:5173/
- Should see the default Vite + React page with a counter button

**What this confirms:**
- ✅ Frontend dev server is running
- ✅ React is working
- ✅ TypeScript is compiling
- ✅ Tailwind CSS is loaded (you'll see styled components)

---

## Step 6: Verify Type Checking

```bash
# With virtual environment activated
make typecheck

# OR manually
mypy spendsense/app
```

**Expected output:**
```
Success: no issues found in X source files
```

**What this confirms:**
- ✅ All Python code is properly typed
- ✅ No type errors in the codebase

---

## Step 7: Run Tests

```bash
# With virtual environment activated
make test

# OR manually
pytest -q
```

**Expected output:**
```
no tests ran in 0.XXs
```

This is correct! We haven't written any tests yet—that comes in later epics.

**What this confirms:**
- ✅ pytest is installed and working
- ✅ Test infrastructure is ready

---

## Troubleshooting

### Port Already in Use

If you see `Address already in use` error:

**Backend:**
```bash
# Change API_PORT in .env file
API_PORT=8001  # or any other available port
```

**Frontend:**
```bash
# Change FRONTEND_PORT in .env file
FRONTEND_PORT=5174  # or any other available port
```

### Module Not Found Errors

Make sure your virtual environment is activated:
```bash
# You should see (.venv) at the start of your terminal prompt
# If not, activate it:
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\Activate.ps1  # Windows
```

### Frontend Build Errors

Clear cache and reinstall:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
```

---

## Quick Reference

### Makefile Commands

```bash
make help           # Show all available commands
make setup          # Complete first-time setup
make backend        # Start backend (port 8000)
make frontend       # Start frontend (port 5173)
make test           # Run tests
make typecheck      # Run type checking
make clean          # Remove build artifacts
```

### Manual Commands

**Backend:**
```bash
# Start server
uvicorn spendsense.app.main:app --reload --host 127.0.0.1 --port 8000

# Run tests
pytest -q

# Type check
mypy spendsense/app
```

**Frontend:**
```bash
# Start dev server
cd frontend && npm run dev

# Build for production
cd frontend && npm run build
```

---

## Project Structure

```
SpendSense/
├── .env                    # Backend environment variables (you create this)
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── Makefile               # Development shortcuts
├── spendsense/
│   └── app/
│       ├── main.py        # FastAPI application entry point
│       ├── core/
│       │   ├── config.py  # Configuration management
│       │   └── logging.py # Logging setup
│       ├── db/            # Database models (future)
│       ├── features/      # Feature engineering (future)
│       ├── personas/      # Persona logic (future)
│       └── api/           # API routes (future)
├── frontend/
│   ├── .env.local         # Frontend environment variables (you create this)
│   ├── src/
│   │   ├── main.tsx       # React entry point
│   │   └── index.css      # Tailwind CSS imports
│   ├── vite.config.ts     # Vite configuration
│   └── package.json       # Node dependencies
└── data/                  # SQLite and Parquet files (auto-created)
```

---

## Success Criteria ✅

You're all set when you can:

- [x] Start backend without errors
- [x] Visit http://127.0.0.1:8000/health and see `{"status":"healthy"}`
- [x] Visit http://127.0.0.1:8000/docs and see API documentation
- [x] Start frontend without errors
- [x] Visit http://localhost:5173/ and see Vite + React page
- [x] Run `mypy spendsense/app` without type errors
- [x] Run `pytest -q` successfully

---

## What's Next?

Now that your development environment is ready, you can start building features:

1. **Epic: Data Foundation** - Generate synthetic transaction data
2. **Epic: Feature Engineering** - Compute behavioral signals
3. **Epic: Persona System** - Assign personas based on signals
4. **Epic: Recommendations** - Build recommendation engine
5. **Epic: Frontend UI** - Create user and operator views

Check `../deployment/TASK_LIST.md` for detailed task breakdown!


