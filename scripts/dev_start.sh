#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Project-W — full local dev environment startup
# Usage: bash scripts/dev_start.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log() { echo -e "${GREEN}[dev]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC} $1"; }

# ── 1. Check venv ─────────────────────────────────────────────
if [ ! -d .venv ]; then
  log "Creating virtual environment..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -q -r shared/requirements.txt -r services/api-server/requirements.txt -r requirements-dev.txt
  for svc in permit-ingester bid-ingester license-scraper etl-pipeline; do
    pip install -q -r services/$svc/requirements.txt
  done
else
  source .venv/bin/activate
fi

# ── 2. Create Python symlinks ─────────────────────────────────
for svc in api-server permit-ingester bid-ingester etl-pipeline license-scraper; do
  mod=$(echo $svc | tr '-' '_')
  test -L services/$mod || ln -s $svc services/$mod
done

# ── 3. Start Firestore emulator ───────────────────────────────
log "Starting Firestore emulator on :8681..."
JAVA_HOME="$(brew --prefix openjdk 2>/dev/null)" || true
export PATH="$JAVA_HOME/bin:$PATH"

if ! curl -s http://localhost:8681 >/dev/null 2>&1; then
  firebase emulators:start --only firestore --project leadgen-mvp-local \
    > /tmp/firestore-emulator.log 2>&1 &
  EMULATOR_PID=$!
  echo $EMULATOR_PID > /tmp/firestore-emulator.pid
  log "Waiting for emulator (PID $EMULATOR_PID)..."
  for i in $(seq 1 15); do
    sleep 2
    if curl -s http://localhost:8681 >/dev/null 2>&1; then
      log "✅ Firestore emulator ready"
      break
    fi
    echo -n "."
  done
else
  log "✅ Firestore emulator already running"
fi

# ── 4. Seed dev data ──────────────────────────────────────────
log "Seeding dev data..."
FIRESTORE_EMULATOR_HOST=localhost:8681 GOOGLE_CLOUD_PROJECT=leadgen-mvp-local \
  PYTHONPATH="$REPO" python scripts/seed_dev_data.py 2>&1 | grep -E "✅|Seeding|Error" || true

# ── 5. Start API server ───────────────────────────────────────
log "Starting API server on :8005..."
kill -9 $(pgrep -f "uvicorn services.api_server" | head -1) 2>/dev/null || true
sleep 1
PYTHONPATH="$REPO" FIRESTORE_EMULATOR_HOST=localhost:8681 GOOGLE_CLOUD_PROJECT=leadgen-mvp-local \
  uvicorn services.api_server.main:app --host 0.0.0.0 --port 8005 \
  > /tmp/api-server.log 2>&1 &
API_PID=$!
echo $API_PID > /tmp/api-server.pid
sleep 3

if curl -s http://localhost:8005/api/health >/dev/null; then
  log "✅ API server ready (PID $API_PID)"
else
  warn "API server might not be ready yet — check /tmp/api-server.log"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  BuildScope dev environment running${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "  API server:  http://localhost:8005"
echo "  Firestore:   http://localhost:8681"
echo "  Frontend:    cd services/api-server/frontend && npm run dev"
echo "  Logs:        tail -f /tmp/api-server.log"
echo "  Stop all:    kill \$(cat /tmp/api-server.pid /tmp/firestore-emulator.pid 2>/dev/null)"
echo ""
