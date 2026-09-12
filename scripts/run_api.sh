#!/usr/bin/env bash
set -euo pipefail

HOST="${MODEL_SCOUT_HOST:-0.0.0.0}"
PORT="${MODEL_SCOUT_PORT:-8080}"

python -m uvicorn src.model_scout_api.main:app --host "$HOST" --port "$PORT"
