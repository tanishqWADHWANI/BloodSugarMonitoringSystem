#!/usr/bin/env bash
# Helper: apply trigger SQL into the running MySQL container named 'bsm-mysql'
# Usage: ./apply_triggers_in_container.sh [container-name]
# If no container name provided, defaults to 'bsm-mysql'.

set -euo pipefail

CONTAINER=${1:-bsm-mysql}
# Resolve SQL file path relative to this script so it works from any CWD
SQL_FILE="$(cd "$(dirname "$0")" >/dev/null && pwd)/sql/fix_triggers.sql"

if ! docker ps --format '{{.Names}}' | grep -q -x "$CONTAINER"; then
  echo "Container '$CONTAINER' not found in running containers."
  echo "Run 'docker ps' to list containers and pass the running MySQL container name as the first argument."
  exit 2
fi

echo "Applying triggers from local file: backend/sql/fix_triggers.sql"
echo "You will be prompted for the MySQL root password when the mysql client runs inside the container."

# Stream the SQL into the mysql client inside the container. This avoids copying files into the container.
if [ ! -f "$SQL_FILE" ]; then
  echo "SQL file not found: $SQL_FILE"
  exit 3
fi
cat "$SQL_FILE" | docker exec -i "$CONTAINER" mysql -u root -p blood_sugar_db

echo "Done. Triggers recreated (or dropped then created)."
