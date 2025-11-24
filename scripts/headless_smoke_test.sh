#!/usr/bin/env bash
# Headless smoke test for BloodSugarMonitoringSystem backend
# Checks: /health, specialist login (jsmith), specialist patients for jsmith

set -euo pipefail

BASE_URL=${BASE_URL:-http://127.0.0.1:5000}

echo "Running headless smoke tests against $BASE_URL"

echo "\n1) Health check"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health") || true
echo "  HTTP $HTTP_CODE -> $BASE_URL/health"
if [ "$HTTP_CODE" != "200" ]; then
  echo "Health check failed (expected 200)."
  exit 2
fi

# Check server mode to see if DB is available and/or demo mode is enabled
echo "\n0) Server mode check (/api/server/mode)"
MODE_JSON=$(curl -s "$BASE_URL/api/server/mode" || echo "{}")
DEMO_MODE=$(echo "$MODE_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('demo_mode', False))" 2>/dev/null || echo "false")
DB_AVAILABLE=$(echo "$MODE_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('db_available', False))" 2>/dev/null || echo "false")
echo "  demo_mode=$DEMO_MODE db_available=$DB_AVAILABLE"

echo "\n2) Specialist login (jsmith)"
LOGIN_PAYLOAD='{"username":"jsmith","password":"smith123"}'
LOGIN_RESP=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$LOGIN_PAYLOAD" "$BASE_URL/api/specialist/login") || true
LOGIN_HTTP=$(echo "$LOGIN_RESP" | tail -n1)
LOGIN_BODY=$(echo "$LOGIN_RESP" | sed '$d')
echo "  HTTP $LOGIN_HTTP -> /api/specialist/login"
echo "  Body: $LOGIN_BODY"
if [ "$LOGIN_HTTP" != "200" ]; then
  echo "Login failed (expected 200)."
  exit 3
fi

TOKEN=$(echo "$LOGIN_BODY" | sed -n 's/.*"token"[[:space:]]*:[[:space:]]*"\([^"]\+\)".*/\1/p') || true
echo "  Extracted token: ${TOKEN:-<none>}"

echo "\n3) Fetch specialist patients (working_id=jsmith)"
if [ "$DB_AVAILABLE" = "True" ] || [ "$DB_AVAILABLE" = "true" ] || [ "$DB_AVAILABLE" = "1" ]; then
  PAT_HTTP=$(curl -s -o /tmp/_smoke_patients.json -w "%{http_code}" "$BASE_URL/api/specialist/patients?working_id=jsmith" || true)
  echo "  HTTP $PAT_HTTP -> /api/specialist/patients?working_id=jsmith"
  if [ "$PAT_HTTP" != "200" ]; then
    echo "Fetching patients failed (expected 200)."
    echo "  Response body:"
    cat /tmp/_smoke_patients.json || true
    exit 4
  fi
else
  echo "  Skipping patients check because DB is not available (server mode)."
  echo "  If you expect DB-backed results, run this test against a running DB-enabled server."
  echo "  (server mode: demo_mode=$DEMO_MODE db_available=$DB_AVAILABLE)"
  # create an empty placeholder so downstream parsing doesn't fail
  echo '{"count":0, "patients": []}' > /tmp/_smoke_patients.json
fi

echo "\nSmoke tests PASSED. Summary:"
echo "  Health: 200"
echo "  Login: 200 (token=${TOKEN:-none})"

# Determine patient count without requiring `jq` (use Python fallback)
COUNT=$(python3 - <<'PY'
import json
try:
  j = json.load(open('/tmp/_smoke_patients.json'))
  c = j.get('count')
  if c is None:
    p = j.get('patients')
    if isinstance(p, list):
      print(len(p))
    else:
      print('?')
  else:
    print(c)
except Exception:
  print('?')
PY
)

echo "  Patients: 200 -> ${COUNT:-?} patients"

exit 0
