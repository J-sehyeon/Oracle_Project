#!/usr/bin/env bash
# ./PoC/scripts/main.sh test1 --extract --device mps
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"


"$SCRIPT_DIR/hpe/hpe.sh" "$@"
"$SCRIPT_DIR/features/features.sh" "$1"
"$SCRIPT_DIR/Agent/agent.sh" "$1"