#!/usr/bin/env bash
set -e

echo "Agent 진입"

FEATURES_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_DIR="$(cd "$FEATURES_DIR/.." && pwd)"
POC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$(cd "$POC_DIR/.." && pwd)"

RUN_FOLDER="$1"
RUN_DIR="$POC_DIR/run/$RUN_FOLDER" 

"$POC_DIR/.venv/bin/python" \
  "$FEATURES_DIR/Running_coach.py" \
  "$PROJECT_DIR" \
  "$RUN_FOLDER" \