#!/usr/bin/env bash
# End-to-end: Tech Economist API + operational-intelligence crew → session cost.
set -euo pipefail

PORT="${TE_PORT:-8765}"
BASE="http://127.0.0.1:${PORT}"
OI_ROOT="${OI_ROOT:-$HOME/Projects/operational-intelligence}"
TE_BACKEND="$(cd "$(dirname "$0")/../backend" && pwd)"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "==> Starting Tech Economist on ${BASE}"
cd "$TE_BACKEND"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$PORT" &
SERVER_PID=$!

for _ in $(seq 1 30); do
  if curl -sf "${BASE}/api/workflows" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

WF_ID=$(curl -sf "${BASE}/api/workflows" | python3 -c "
import json, sys
for w in json.load(sys.stdin):
    if w['name'] == 'Operational Intelligence Crew':
        print(w['id'])
        break
")
if [[ -z "${WF_ID}" ]]; then
  echo "ERROR: Operational Intelligence Crew workflow not found" >&2
  exit 1
fi
echo "==> Workflow id: ${WF_ID}"

echo "==> Running OI content crew"
export OI_TECH_ECONOMIST_URL="$BASE"
export OI_TECH_ECONOMIST_WORKFLOW_ID="$WF_ID"
OUT=$(cd "$OI_ROOT" && cargo run -q -p oi-cli -- crew "integration test topic" --no-approval 2>/dev/null)
SESSION_ID=$(echo "$OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['workflow_id'])")

echo "==> Session ${SESSION_ID}"
COST=$(curl -sf "${BASE}/api/sessions/${SESSION_ID}/cost")
echo "$COST" | python3 -m json.tool

echo "$COST" | python3 -c "
import json, sys
c = json.load(sys.stdin)
assert c['call_count'] == 4, c
assert c['total_cost_usd'] > 0, c
agents = set(c['by_agent'])
expected = {'research-agent', 'analyst-agent', 'writer-agent', 'editor-agent'}
assert agents == expected, (agents, expected)
print('OK: 4 calls, all agents, total_cost_usd =', c['total_cost_usd'])
"
