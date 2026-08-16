#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-rtmpose"
MMPPOSE_DIR="$ROOT_DIR/mmpose"
MMDET_DIR="$ROOT_DIR/mmdetection"
XTCOCO_DIR="$ROOT_DIR/xtcocoapi"
MMPPOSE_REF="v1.3.2"
MMDET_REF="v3.2.0"
XTCOCO_REF="v1.14.3"
PYTHON_VERSION="${RTMPOSE_PYTHON_VERSION:-3.12}"

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "Virtual environment: $VENV_DIR (Python $PYTHON_VERSION)"
  echo "MMPose: https://github.com/open-mmlab/mmpose.git @ $MMPPOSE_REF"
  echo "MMDetection: https://github.com/open-mmlab/mmdetection.git @ $MMDET_REF"
  echo "xtcocotools source: https://github.com/jin-s13/xtcocoapi.git @ $XTCOCO_REF"
  echo "Dependencies: setuptools<81 torch torchvision openmim mmengine mmcv==2.1.0"
  echo "MMCV build isolation: disabled (uses setuptools<81 for OpenMIM compatibility)"
  echo "Editable package build isolation: disabled (exposes installed PyTorch)"
  echo "MMDetection .mim config links: enabled for mmdet:: config inheritance"
  echo "MMPose .mim config links: enabled for mmpose:: config inheritance"
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

if [[ ! -d "$XTCOCO_DIR/.git" ]]; then
  git clone https://github.com/jin-s13/xtcocoapi.git "$XTCOCO_DIR"
fi
git -C "$XTCOCO_DIR" fetch --tags --force
git -C "$XTCOCO_DIR" checkout --detach "$XTCOCO_REF"

PYTHON_BIN="$VENV_DIR/bin/python"
uv pip install --python "$PYTHON_BIN" --upgrade pip "setuptools<81" wheel
uv pip install --python "$PYTHON_BIN" torch torchvision openmim
uv pip install --python "$PYTHON_BIN" "mmengine>=0.7.1,<1.0.0"
"$PYTHON_BIN" -m pip install --no-build-isolation "mmcv==2.1.0"
uv pip install --python "$PYTHON_BIN" cython
"$PYTHON_BIN" -m pip install --no-build-isolation "$XTCOCO_DIR"
uv pip install --python "$PYTHON_BIN" --no-build-isolation -v -e "$MMDET_DIR" -e "$MMPPOSE_DIR"

MMDET_PACKAGE_DIR="$("$PYTHON_BIN" - <<'PY'
import mmdet

print(next(iter(mmdet.__path__)))
PY
)"
SITE_PACKAGES_DIR="$("$PYTHON_BIN" - <<'PY'
import site

print(site.getsitepackages()[0])
PY
)"
for MIM_DIR in "$MMDET_PACKAGE_DIR/.mim" "$SITE_PACKAGES_DIR/mmdet/.mim"; do
  mkdir -p "$MIM_DIR"
  ln -sfn "$MMDET_DIR/configs" "$MIM_DIR/configs"
  ln -sfn "$MMDET_DIR/model-index.yml" "$MIM_DIR/model-index.yml"
done

MMPOSE_PACKAGE_DIR="$("$PYTHON_BIN" - <<'PY'
import os
import mmpose

print(next(iter(mmpose.__path__)))
PY
)"
for MIM_DIR in "$MMPOSE_PACKAGE_DIR/.mim" "$SITE_PACKAGES_DIR/mmpose/.mim"; do
  mkdir -p "$MIM_DIR"
  ln -sfn "$MMPPOSE_DIR/configs" "$MIM_DIR/configs"
  ln -sfn "$MMPPOSE_DIR/model-index.yml" "$MIM_DIR/model-index.yml"
done

echo "RTMPose MPS environment installed: $VENV_DIR"
