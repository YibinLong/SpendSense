# SpendSense Makefile
# Simple shortcuts for common development tasks

# Default shell
SHELL := /bin/bash

# Python commands
.PHONY: venv
venv:
	@echo "Creating Python virtual environment..."
	python -m venv .venv
	@echo "✓ Virtual environment created"
	@echo "Activate with: source .venv/bin/activate (macOS/Linux) or .venv\\Scripts\\Activate.ps1 (Windows)"

.PHONY: install
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✓ Python dependencies installed"

.PHONY: backend
backend:
	@echo "Starting FastAPI backend on http://127.0.0.1:8000..."
	uvicorn spendsense.app.main:app --reload --host 127.0.0.1 --port 8000

.PHONY: test
test:
	@echo "Running tests with pytest..."
	pytest -q

.PHONY: typecheck
typecheck:
	@echo "Running mypy type checks..."
	mypy spendsense/app

.PHONY: lint
lint:
	@echo "Running ruff linter..."
	ruff check spendsense/

.PHONY: lint-fix
lint-fix:
	@echo "Running ruff linter with auto-fix..."
	ruff check --fix spendsense/

# Frontend commands
.PHONY: frontend-install
frontend-install:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ Frontend dependencies installed"

.PHONY: frontend
frontend:
	@echo "Starting frontend dev server on http://localhost:5173..."
	cd frontend && npm run dev

.PHONY: frontend-build
frontend-build:
	@echo "Building frontend for production..."
	cd frontend && npm run build

# Combined commands
.PHONY: install-all
install-all: install frontend-install
	@echo "✓ All dependencies installed"

.PHONY: setup
setup: venv install frontend-install
	@echo ""
	@echo "✓ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Activate venv: source .venv/bin/activate"
	@echo "  2. Create .env file in project root (see PRD.md for contents)"
	@echo "  3. Create frontend/.env.local with VITE_API_BASE=http://127.0.0.1:8000"
	@echo "  4. Run backend: make backend"
	@echo "  5. Run frontend: make frontend (in another terminal)"

.PHONY: clean
clean:
	@echo "Cleaning up build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist frontend/.vite 2>/dev/null || true
	@echo "✓ Cleaned"

.PHONY: help
help:
	@echo "SpendSense Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make venv             - Create Python virtual environment"
	@echo "  make install          - Install Python dependencies"
	@echo "  make frontend-install - Install frontend dependencies"
	@echo "  make install-all      - Install all dependencies"
	@echo "  make setup            - Complete first-time setup"
	@echo ""
	@echo "Development:"
	@echo "  make backend          - Start FastAPI backend (port 8000)"
	@echo "  make frontend         - Start Vite dev server (port 5173)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test             - Run pytest"
	@echo "  make typecheck        - Run mypy type checking"
	@echo "  make lint             - Run ruff linter"
	@echo "  make lint-fix         - Run ruff linter with auto-fix"
	@echo ""
	@echo "Build:"
	@echo "  make frontend-build   - Build frontend for production"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            - Remove build artifacts"
	@echo "  make help             - Show this help message"

# Default target
.DEFAULT_GOAL := help


