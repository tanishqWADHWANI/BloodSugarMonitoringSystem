#!/usr/bin/env bash
# Generate a self-signed TLS certificate for local development.
# Places files in backend/certs/server.crt and backend/certs/server.key

set -euo pipefail

OUT_DIR="$(cd "$(dirname "$0")" >/dev/null && pwd)/certs"
CRT="$OUT_DIR/server.crt"
KEY="$OUT_DIR/server.key"

mkdir -p "$OUT_DIR"

if [ -f "$CRT" -a -f "$KEY" ]; then
  echo "Certificate and key already exist at $CRT and $KEY"
  exit 0
fi

echo "Generating self-signed certificate for localhost..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$KEY" -out "$CRT" \
  -subj "/C=US/ST=None/L=None/O=BSM/OU=Dev/CN=localhost"

echo "Wrote: $CRT and $KEY"
echo "Note: browsers will show a warning for self-signed certs unless you add them to trust store."
#!/usr/bin/env bash
# Generate a self-signed TLS certificate for local development.
# Places files in backend/certs/server.crt and backend/certs/server.key

set -euo pipefail

OUT_DIR="$(cd "$(dirname "$0")" >/dev/null && pwd)/certs"
CRT="$OUT_DIR/server.crt"
KEY="$OUT_DIR/server.key"

mkdir -p "$OUT_DIR"

if [ -f "$CRT" -a -f "$KEY" ]; then
  echo "Certificate and key already exist at $CRT and $KEY"
  exit 0
fi

echo "Generating self-signed certificate for localhost..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$KEY" -out "$CRT" \
  -subj "/C=US/ST=None/L=None/O=BSM/OU=Dev/CN=localhost"

echo "Wrote: $CRT and $KEY"
echo "Note: browsers will show a warning for self-signed certs unless you add them to trust store."
