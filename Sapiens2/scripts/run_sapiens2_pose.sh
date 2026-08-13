#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-sapiens2"
PYTHON_BIN="$VENV_DIR/bin/python"
POSE_ROOT="$ROOT_DIR/sapiens2/sapiens/pose"
CONFIG_FILE="$POSE_ROOT/configs/keypoints308/shutterstock_goliath_3po/sapiens2_0.4b_keypoints308_shutterstock_goliath_3po-1024x768.py"
CHECKPOINT_FILE="$ROOT_DIR/models/sapiens2/pose/sapiens2_0.4b_pose.safetensors"
DETECTOR_DIR="$ROOT_DIR/models/sapiens2/detector/detr-resnet-101-dc5"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 [--dry-run] INPUT_DIR [OUTPUT_DIR]" >&2
  exit 2  
fi

INPUT_DIR="$1"
OUTPUT_DIR="${2:-$ROOT_DIR/outputs/sapiens2/pose}"
PREFERRED_DEVICE="${SAPIENS2_DEVICE:-auto}"

if [[ ! -d "$INPUT_DIR" ]]; then
  echo "Input directory does not exist: $INPUT_DIR" >&2
  exit 1
fi

INPUT_DIR="$(cd "$INPUT_DIR" && pwd -P)"
if [[ "$OUTPUT_DIR" != /* ]]; then
  OUTPUT_DIR="$PWD/$OUTPUT_DIR"
fi

if [[ $DRY_RUN -eq 1 ]]; then
  DEVICE="$PREFERRED_DEVICE"
else
  for required in "$PYTHON_BIN" "$CONFIG_FILE" "$CHECKPOINT_FILE" "$DETECTOR_DIR/config.json" "$DETECTOR_DIR/model.safetensors"; do
    if [[ ! -e "$required" ]]; then
      echo "Missing required file: $required" >&2
      exit 1
    fi
  done

  DEVICE="$(PYTHONPATH="$ROOT_DIR" "$PYTHON_BIN" - "$PREFERRED_DEVICE" <<'PY'
import sys

from scripts.sapiens2_runtime import select_device

print(select_device(sys.argv[1]))
PY
)"

  PYTHONPATH="$ROOT_DIR" "$PYTHON_BIN" - "$CHECKPOINT_FILE" <<'PY'
import sys

from scripts.sapiens2_runtime import validate_safetensors_file

print(f"Checkpoint dtypes: {validate_safetensors_file(sys.argv[1])}")
PY
fi

mkdir -p "$OUTPUT_DIR" "$ROOT_DIR/.cache/matplotlib"
export PYTORCH_ENABLE_MPS_FALLBACK=1
export MPLCONFIGDIR="$ROOT_DIR/.cache/matplotlib"
export PYTHONPATH="$ROOT_DIR/sapiens2:$ROOT_DIR"

COMMAND=(
  "$PYTHON_BIN" tools/vis/vis_pose.py
  "$DETECTOR_DIR"
  "$CONFIG_FILE"
  "$CHECKPOINT_FILE"
  --input "$INPUT_DIR"
  --output "$OUTPUT_DIR"
  --device "$DEVICE"
  --radius 4
  --thickness 3
  --kpt-thr 0.3
)

echo "Quantization: disabled; checkpoint precision is preserved"
printf 'PYTORCH_ENABLE_MPS_FALLBACK=1 '
printf '%q ' "${COMMAND[@]}"
printf '\n'

if [[ $DRY_RUN -eq 1 ]]; then
  exit 0
fi

cd "$POSE_ROOT"
"${COMMAND[@]}"
