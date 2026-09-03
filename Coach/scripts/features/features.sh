#!/usr/bin/env bash
set -e

echo "Features 진입"

FEATURES_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_DIR="$(cd "$FEATURES_DIR/.." && pwd)"
COACH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo $FEATURES_DIR
echo $COACH_DIR

RUN_FOLDER="$1"

"$COACH_DIR/.venv/bin/python" \
  "$FEATURES_DIR/feature_extract.py" \
  "$COACH_DIR" \
  "$RUN_FOLDER" \