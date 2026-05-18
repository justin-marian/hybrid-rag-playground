#!/usr/bin/env bash

# Override host/port via env vars: API_HOST, API_PORT.
set -euo pipefail

export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-8001}"

python -m uvicorn app:app \
    --reload \
    --host "$API_HOST" \
    --port "$API_PORT"
