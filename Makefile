.PHONY: setup test-unit test-integration test-e2e test-all coverage lint lint-fix typecheck build up down logs clean

SHELL := /bin/bash
export MSYS_NO_PATHCONV=1

# ---- Setup ----
setup:
	python -m venv .venv
	.venv/Scripts/pip install --upgrade pip
	.venv/Scripts/pip install -r requirements-dev.txt
	.venv/Scripts/pip install -r shared/requirements.txt
	@for svc in permit-ingester bid-ingester license-scraper etl-pipeline api-server; do \
		.venv/Scripts/pip install -r services/$$svc/requirements.txt; \
	done
	cd services/api-server/frontend && npm install

# ---- Testing ----
test-unit:
	.venv/Scripts/pytest tests/unit -v --tb=short -m unit

test-integration:
	docker compose -f docker-compose.test.yml up -d firestore-emulator
	@echo "Waiting for Firestore emulator..."
	@sleep 3
	FIRESTORE_EMULATOR_HOST=localhost:8681 .venv/Scripts/pytest tests/integration -v --tb=short -m integration
	docker compose -f docker-compose.test.yml down

test-e2e:
	docker compose up -d
	@echo "Waiting for services..."
	@sleep 8
	.venv/Scripts/pytest tests/e2e -v --tb=short -m e2e
	docker compose down

test-all: test-unit test-integration

coverage:
	.venv/Scripts/pytest tests/unit tests/integration --cov --cov-report=html --cov-report=xml -m "unit or integration"

# ---- Quality ----
lint:
	.venv/Scripts/ruff check .
	.venv/Scripts/ruff format --check .

lint-fix:
	.venv/Scripts/ruff check --fix .
	.venv/Scripts/ruff format .

typecheck:
	.venv/Scripts/mypy shared/ services/

# ---- Docker ----
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage coverage.xml
