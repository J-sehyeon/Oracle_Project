#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv-rtmpose/bin/python"
VARIANT="${RTMPOSE_VARIANT:-m}"
PREFERRED_DEVICE="${RTMPOSE_DEVICE:-auto}"
KPT_THR="${RTMPOSE_KPT_THR:-0.3}"
BBOX_THR="${RTMPOSE_BBOX_THR:-0.3}"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 [--dry-run] INPUT_DIR [OUTPUT_DIR]" >&2
  exit 2
fi
if [[ "$VARIANT" != "m" && "$VARIANT" != "s" ]]; then
  echo "RTMPOSE_VARIANT must be one of: m, s" >&2
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

POSE_CONFIG="$ROOT_DIR/mmpose/projects/rtmpose/rtmpose/body_2d_keypoint/rtmpose-$VARIANT"_8xb256-420e_coco-256x192.py
DETECTOR_CONFIG="$ROOT_DIR/mmpose/projects/rtmpose/rtmdet/person/rtmdet_nano_320-8xb32_coco-person.py"
if [[ "$VARIANT" == "m" ]]; then
  POSE_CHECKPOINT="$ROOT_DIR/models/rtmpose/rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth"
else
  POSE_CHECKPOINT="$ROOT_DIR/models/rtmpose/rtmpose-s_simcc-coco_pt-aic-coco_420e-256x192-8edcf0d7_20230127.pth"
fi
DETECTOR_CHECKPOINT="$ROOT_DIR/models/rtmdet-nano/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"

COMMAND=(
  "$PYTHON_BIN" -m scripts.rtmpose_infer "$INPUT_DIR" "$OUTPUT_DIR"
  --device "$DEVICE" --variant "$VARIANT" --kpt-thr "$KPT_THR" --bbox-thr "$BBOX_THR"
)

echo "Pose output: 17 body keypoints"
echo "Pose model config: $(basename "$POSE_CONFIG")"
printf '%q ' "${COMMAND[@]}"
printf '\n'

if [[ $DRY_RUN -eq 1 ]]; then
  exit 0
fi

for required in "$PYTHON_BIN" "$POSE_CONFIG" "$DETECTOR_CONFIG" "$POSE_CHECKPOINT" "$DETECTOR_CHECKPOINT"; do
  if [[ ! -e "$required" ]]; then
    echo "Missing required file: $required" >&2
    exit 1
  fi
done

mkdir -p "$OUTPUT_DIR"
export PYTHONPATH="$ROOT_DIR:$ROOT_DIR/mmpose:$ROOT_DIR/mmdetection${PYTHONPATH:+:$PYTHONPATH}"
"${COMMAND[@]}"
