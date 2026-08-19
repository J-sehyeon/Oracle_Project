#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv-rtmpose/bin/python"
MODELS_DIR="$ROOT_DIR/models"
HPE_MODEL="${RTMPOSE_HPE_MODEL:-rtmw}"

case "$HPE_MODEL" in
  rtmw)
    HPE_REQUIREMENT="RTMW-X model via Transformers / Hugging Face"
    HPE_CHECKPOINT=""
    ;;
  halpe26)
    HPE_REQUIREMENT="RTMPose-M Halpe-26 checkpoint"
    HPE_CHECKPOINT="$MODELS_DIR/rtmpose/rtmpose-m_simcc-body7_pt-body7-halpe26_700e-384x288-89e6428b_20230605.pth"
    ;;
  *)
    echo "RTMPOSE_HPE_MODEL must be rtmw or halpe26" >&2
    exit 2
    ;;
esac

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "Python virtual environment"
  echo "PyTorch MPS build and runtime availability"
  echo "MMPose and MMDetection imports"
  echo "RTMDet-nano checkpoint"
  echo "HPE model: $HPE_MODEL"
  echo "$HPE_REQUIREMENT"
  echo "Transformers runtime"
  exit 0
fi

if [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--dry-run]" >&2
  exit 2
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing Python environment: $PYTHON_BIN. Run scripts/install_rtmpose_mps.sh first." >&2
  exit 1
fi

for required in "$MODELS_DIR/rtmdet-nano/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"; do
  if [[ ! -f "$required" ]]; then
    echo "Missing model file: $required. Run scripts/download_rtmw_models.sh first." >&2
    exit 1
  fi
done

if [[ -n "$HPE_CHECKPOINT" && ! -f "$HPE_CHECKPOINT" ]]; then
  echo "Missing model file: $HPE_CHECKPOINT. Run scripts/download_rtmw_models.sh first." >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import platform
from importlib.metadata import version

import torch

print(f"Python: {platform.python_version()} ({platform.machine()})")
print(f"PyTorch: {torch.__version__}")
print(f"MPS built: {torch.backends.mps.is_built()}")
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"MMDetection: {version('mmdet')}")
print(f"MMPose: {version('mmpose')}")
print(f"Transformers: {version('transformers')}")

if not torch.backends.mps.is_built() or not torch.backends.mps.is_available():
    raise SystemExit("MPS is required for auto execution but is unavailable.")
PY

echo "Environment check: OK"
