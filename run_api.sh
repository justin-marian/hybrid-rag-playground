#!/usr/bin/env bash

# Override host/port via env vars: API_HOST, API_PORT.
set -euo pipefail

HOST="${API_HOST:-0.0.0.0}"
PORT="${API_PORT:-8000}"

exec uvicorn app:app --host "$HOST" --port "$PORT" --reload
