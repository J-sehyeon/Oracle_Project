#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv-sapiens2/bin/python"
POSE_CHECKPOINT="$ROOT_DIR/models/sapiens2/pose/sapiens2_0.4b_pose.safetensors"
DETECTOR_CHECKPOINT="$ROOT_DIR/models/sapiens2/detector/detr-resnet-101-dc5/model.safetensors"

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "Python 3.12 virtual environment"
  echo "PyTorch import and version"
  echo "Apple MPS build and runtime availability"
  echo "Sapiens2 editable package import"
  echo "Checkpoint dtype validation (pose and detector)"
  exit 0
fi

if [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--dry-run]" >&2
  exit 2
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing Python environment: $PYTHON_BIN" >&2
  exit 1
fi

export MPLCONFIGDIR="$ROOT_DIR/.cache/matplotlib"
export PYTHONPATH="$ROOT_DIR/sapiens2:$ROOT_DIR"

"$PYTHON_BIN" - "$POSE_CHECKPOINT" "$DETECTOR_CHECKPOINT" <<'PY'
import platform
import sys
from pathlib import Path

import torch

import sapiens  # noqa: F401
from scripts.sapiens2_runtime import validate_safetensors_file

if sys.version_info < (3, 12):
    raise SystemExit(f"Python 3.12+ is required; found {platform.python_version()}")

print(f"Python: {platform.python_version()} ({platform.machine()})")
print(f"PyTorch: {torch.__version__}")
print(f"MPS built: {torch.backends.mps.is_built()}")
print(f"MPS available: {torch.backends.mps.is_available()}")
print("Sapiens2 import: OK")

for name, raw_path in zip(("pose", "detector"), sys.argv[1:], strict=True):
    path = Path(raw_path)
    if not path.is_file():
        raise SystemExit(f"Missing {name} checkpoint: {path}")
    print(f"Checkpoint dtype ({name}): {validate_safetensors_file(path)}")

print("Environment check: OK")
PY

echo "Sapiens2 upstream commit: $(git -C "$ROOT_DIR/sapiens2" rev-parse HEAD)"
