#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv-rtmpose/bin/python"
PREFERRED_DEVICE="${RTMPOSE_DEVICE:-auto}"
KPT_THR="${RTMPOSE_KPT_THR:-0.3}"
BBOX_THR="${RTMPOSE_BBOX_THR:-0.3}"
RTMW_MODEL_ID="akore/rtmw-x-384x288"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 [--dry-run] INPUT_DIR [OUTPUT_DIR]" >&2
  exit 2
fi
if [[ "$PREFERRED_DEVICE" == "auto" ]]; then
  DEVICE="mps"
elif [[ "$PREFERRED_DEVICE" == "mps" || "$PREFERRED_DEVICE" == "cpu" ]]; then
  DEVICE="$PREFERRED_DEVICE"
else
  echo "RTMPOSE_DEVICE must be auto, mps, or cpu" >&2
  exit 2
fi

INPUT_DIR="$1"
OUTPUT_DIR="${2:-$ROOT_DIR/outputs/pose}"
if [[ ! -d "$INPUT_DIR" ]]; then
  echo "Input directory does not exist: $INPUT_DIR" >&2
  exit 1
fi
INPUT_DIR="$(cd "$INPUT_DIR" && pwd -P)"
if [[ "$OUTPUT_DIR" != /* ]]; then
  OUTPUT_DIR="$PWD/$OUTPUT_DIR"
fi

DETECTOR_CONFIG="$ROOT_DIR/mmpose/projects/rtmpose/rtmdet/person/rtmdet_nano_320-8xb32_coco-person.py"
DETECTOR_CHECKPOINT="$ROOT_DIR/models/rtmdet-nano/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"

COMMAND=(
  "$PYTHON_BIN" -m scripts.rtmw_infer "$INPUT_DIR" "$OUTPUT_DIR"
  --device "$DEVICE" --kpt-thr "$KPT_THR" --bbox-thr "$BBOX_THR"
)

echo "Pose output: 133 whole-body keypoints"
echo "Pose model: RTMW-X ($RTMW_MODEL_ID)"
printf '%q ' "${COMMAND[@]}"
printf '\n'

if [[ $DRY_RUN -eq 1 ]]; then
  exit 0
fi

for required in "$PYTHON_BIN" "$DETECTOR_CONFIG" "$DETECTOR_CHECKPOINT"; do
  if [[ ! -e "$required" ]]; then
    echo "Missing required file: $required" >&2
    exit 1
  fi
done

mkdir -p "$OUTPUT_DIR"
export PYTHONPATH="$ROOT_DIR:$ROOT_DIR/mmpose:$ROOT_DIR/mmdetection${PYTHONPATH:+:$PYTHONPATH}"
"${COMMAND[@]}"
