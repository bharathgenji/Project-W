.PHONY: setup test-unit test-integration test-e2e test-all coverage lint lint-fix typecheck build up down logs clean

SHELL := /bin/bash
export MSYS_NO_PATHCONV=1

# Detect OS: use Scripts/ on Windows, bin/ on Unix
ifeq ($(OS),Windows_NT)
	VENV_BIN := .venv/Scripts
else
	VENV_BIN := .venv/bin
endif

# ---- Setup ----
setup:
	python3 -m venv .venv
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements-dev.txt
	$(VENV_BIN)/pip install -r shared/requirements.txt
	@for svc in permit-ingester bid-ingester license-scraper etl-pipeline api-server; do \
		$(VENV_BIN)/pip install -r services/$$svc/requirements.txt; \
	done
	@# Create Python-importable symlinks — hyphenated dir names aren't valid module names
	@for svc in api-server permit-ingester bid-ingester etl-pipeline license-scraper; do \
		mod=$$(echo $$svc | tr '-' '_'); \
		test -L services/$$mod || ln -s $$svc services/$$mod; \
	done
	cd services/api-server/frontend && npm install

# ---- Testing ----
test-unit:
	PYTHONPATH=$(PWD) $(VENV_BIN)/pytest tests/unit -v --tb=short -m unit

test-integration:
	docker compose -f docker-compose.test.yml up -d firestore-emulator
	@echo "Waiting for Firestore emulator..."
	@sleep 5
	PYTHONPATH=$(PWD) FIRESTORE_EMULATOR_HOST=localhost:8681 $(VENV_BIN)/pytest tests/integration -v --tb=short -m integration
	docker compose -f docker-compose.test.yml down

test-e2e:
	docker compose up -d
	@echo "Waiting for services..."
	@sleep 8
	PYTHONPATH=$(PWD) $(VENV_BIN)/pytest tests/e2e -v --tb=short -m e2e
	docker compose down

test-all: test-unit test-integration

coverage:
	PYTHONPATH=$(PWD) $(VENV_BIN)/pytest tests/unit tests/integration --cov --cov-report=html --cov-report=xml -m "unit or integration"

# ---- Quality ----
lint:
	$(VENV_BIN)/ruff check .
	$(VENV_BIN)/ruff format --check .

lint-fix:
	$(VENV_BIN)/ruff check --fix .
	$(VENV_BIN)/ruff format .

typecheck:
	$(VENV_BIN)/mypy shared/ services/

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
