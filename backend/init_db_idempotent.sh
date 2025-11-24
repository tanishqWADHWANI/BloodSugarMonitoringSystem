#!/usr/bin/env bash
# Idempotent DB initialization helper
# Usage:
#   ./backend/init_db_idempotent.sh [mysql-container]
# If a running MySQL container is provided (default: bsm-mysql), the script will
# check for presence of a core table and only import `blood_sugar_db.sql` when
# the schema appears missing. It will always apply `backend/sql/fix_triggers.sql`.

set -euo pipefail

CONTAINER=${1:-bsm-mysql}
ROOT_USER=${DB_ROOT_USER:-root}
# Try to pick up password from container env if available; otherwise prompt.
ROOT_PASS=${DB_ROOT_PASSWORD:-}

SQL_DUMP="$(cd "$(dirname "$0")" >/dev/null && cd .. && pwd)/backend/blood_sugar_db.sql"
FIX_TRIGGERS="$(cd "$(dirname "$0")" >/dev/null && cd .. && pwd)/backend/sql/fix_triggers.sql"

if ! docker ps --format '{{.Names}}' | grep -q -x "$CONTAINER"; then
  echo "Container '$CONTAINER' not found. Please pass a running MySQL container name."
  exit 2
fi

echo "Checking if database schema exists (users table)..."

if [ -z "$ROOT_PASS" ]; then
  # try to read MYSQL_ROOT_PASSWORD from container env
  ROOT_PASS=$(docker inspect "$CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E '^MYSQL_ROOT_PASSWORD=' | sed 's/^MYSQL_ROOT_PASSWORD=//') || true
fi

MYSQL_CMD=(docker exec -i "$CONTAINER" mysql -u "$ROOT_USER")
if [ -n "$ROOT_PASS" ]; then
  MYSQL_CMD+=( -p"$ROOT_PASS" )
else
  echo "No root password found in env; mysql client inside container will prompt for it if required."
fi

# Check for existence of `users` table in `blood_sugar_db`
if printf "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='blood_sugar_db' AND table_name='users';\n" | "${MYSQL_CMD[@]}" blood_sugar_db | tail -n1 | grep -q '^0$'; then
  echo "No schema detected. Importing full SQL dump: $SQL_DUMP"
  if [ ! -f "$SQL_DUMP" ]; then
    echo "SQL dump not found at $SQL_DUMP"
    exit 3
  fi
  cat "$SQL_DUMP" | docker exec -i "$CONTAINER" mysql -u "$ROOT_USER" ${ROOT_PASS:+-p$ROOT_PASS}
else
  echo "Schema appears present; skipping full SQL import."
fi

# Always apply trigger fixes (idempotent)
if [ ! -f "$FIX_TRIGGERS" ]; then
  echo "Trigger SQL not found: $FIX_TRIGGERS"
  exit 4
fi

echo "Applying triggers from $FIX_TRIGGERS"
cat "$FIX_TRIGGERS" | docker exec -i "$CONTAINER" mysql -u "$ROOT_USER" ${ROOT_PASS:+-p$ROOT_PASS} blood_sugar_db

echo "Initialization complete."
