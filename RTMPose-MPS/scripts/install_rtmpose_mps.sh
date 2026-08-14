#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-rtmpose"
MMPPOSE_DIR="$ROOT_DIR/mmpose"
MMDET_DIR="$ROOT_DIR/mmdetection"
MMPPOSE_REF="v1.3.2"
MMDET_REF="v3.2.0"
PYTHON_VERSION="${RTMPOSE_PYTHON_VERSION:-3.12}"

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "Virtual environment: $VENV_DIR (Python $PYTHON_VERSION)"
  echo "MMPose: https://github.com/open-mmlab/mmpose.git @ $MMPPOSE_REF"
  echo "MMDetection: https://github.com/open-mmlab/mmdetection.git @ $MMDET_REF"
  echo "Dependencies: torch torchvision openmim mmengine mmcv==2.1.0"
  exit 0
fi

if [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--dry-run]" >&2
  exit 2
fi

command -v uv >/dev/null 2>&1 || {
  echo "uv is required. Install it first, then rerun this script." >&2
  exit 1
}
command -v git >/dev/null 2>&1 || {
  echo "git is required. Install it first, then rerun this script." >&2
  exit 1
}

if [[ ! -d "$VENV_DIR" ]]; then
  uv venv --python "$PYTHON_VERSION" "$VENV_DIR"
fi

for spec in "$MMPPOSE_DIR https://github.com/open-mmlab/mmpose.git $MMPPOSE_REF" "$MMDET_DIR https://github.com/open-mmlab/mmdetection.git $MMDET_REF"; do
  read -r target url ref <<<"$spec"
  if [[ ! -d "$target/.git" ]]; then
    git clone "$url" "$target"
  fi
  git -C "$target" fetch --tags --force
  git -C "$target" checkout --detach "$ref"
done

PYTHON_BIN="$VENV_DIR/bin/python"
uv pip install --python "$PYTHON_BIN" --upgrade pip setuptools wheel
uv pip install --python "$PYTHON_BIN" torch torchvision openmim
"$PYTHON_BIN" -m mim install "mmengine>=0.7.1,<1.0.0" "mmcv==2.1.0"
uv pip install --python "$PYTHON_BIN" -v -e "$MMDET_DIR" -e "$MMPPOSE_DIR"

echo "RTMPose MPS environment installed: $VENV_DIR"
