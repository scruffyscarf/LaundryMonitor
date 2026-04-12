#!/usr/bin/env bash
# Start FastAPI (uvicorn) then Streamlit. Press Ctrl+C to stop both.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

cd "$ROOT/backend"
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload &
UV_PID=$!

cleanup() {
  kill "$UV_PID" 2>/dev/null || true
  wait "$UV_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if ! python3 -c "
import socket, time
for _ in range(60):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        if s.connect_ex(('127.0.0.1', 8000)) == 0:
            raise SystemExit(0)
    finally:
        s.close()
    time.sleep(0.1)
raise SystemExit(1)
"; then
  echo "error: backend did not accept connections on 127.0.0.1:8000" >&2
  exit 1
fi

cd "$ROOT/frontend"
streamlit run app.py "$@"
