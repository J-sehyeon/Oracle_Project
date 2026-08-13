#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-sapiens2"
HF_BIN="$VENV_DIR/bin/hf"
PYTHON_BIN="$VENV_DIR/bin/python"
MODEL_DIR="$ROOT_DIR/models/sapiens2"
POSE_DIR="$MODEL_DIR/pose"
DETECTOR_DIR="$MODEL_DIR/detector/detr-resnet-101-dc5"
POSE_REPO="facebook/sapiens2-pose-0.4b"
POSE_FILE="sapiens2_0.4b_pose.safetensors"
DETECTOR_REPO="facebook/detr-resnet-101-dc5"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

if [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--dry-run]" >&2
  exit 2
fi

echo "Sapiens2 pose checkpoint: $POSE_REPO/$POSE_FILE"
echo "Person detector: $DETECTOR_REPO"
echo "Quantization: disabled (official floating-point safetensors only)"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "$HF_BIN download $POSE_REPO $POSE_FILE --local-dir $POSE_DIR"
  echo "$HF_BIN download $DETECTOR_REPO --include config.json --include preprocessor_config.json --include model.safetensors --local-dir $DETECTOR_DIR"
  exit 0
fi

if [[ ! -x "$HF_BIN" || ! -x "$PYTHON_BIN" ]]; then
  echo "Missing environment at $VENV_DIR. Run the project setup first." >&2
  exit 1
fi

mkdir -p "$POSE_DIR" "$DETECTOR_DIR" "$ROOT_DIR/.cache/huggingface"
export HF_HOME="$ROOT_DIR/.cache/huggingface"

"$HF_BIN" download "$POSE_REPO" "$POSE_FILE" --local-dir "$POSE_DIR"
"$HF_BIN" download "$DETECTOR_REPO" \
  --include config.json \
  --include preprocessor_config.json \
  --include model.safetensors \
  --local-dir "$DETECTOR_DIR"

PYTHONPATH="$ROOT_DIR" "$PYTHON_BIN" - \
  "$POSE_DIR/$POSE_FILE" \
  "$DETECTOR_DIR/model.safetensors" <<'PY'
import sys

from scripts.sapiens2_runtime import validate_safetensors_file

for checkpoint in sys.argv[1:]:
    counts = validate_safetensors_file(checkpoint)
    print(f"Validated checkpoint dtypes ({checkpoint}): {counts}")
PY

echo "Models are ready in $MODEL_DIR"
