#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT_DIR/models"
RTMDET_FILE="rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"
RTMDET_URL="https://download.openmmlab.com/mmpose/v1/projects/rtmpose/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"
RTMPOSE_M_FILE="rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth"
RTMPOSE_M_URL="https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/$RTMPOSE_M_FILE"
RTMPOSE_S_FILE="rtmpose-s_simcc-coco_pt-aic-coco_420e-256x192-8edcf0d7_20230127.pth"
RTMPOSE_S_URL="https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/$RTMPOSE_S_FILE"

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "RTMDet-nano: $RTMDET_URL"
  echo "RTMPose-M: $RTMPOSE_M_URL"
  echo "RTMPose-S: $RTMPOSE_S_URL"
  exit 0
fi

if [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--dry-run]" >&2
  exit 2
fi

command -v curl >/dev/null 2>&1 || {
  echo "curl is required. Install it first, then rerun this script." >&2
  exit 1
}

download() {
  local url="$1"
  local path="$2"

  if [[ -f "$path" ]]; then
    echo "Already present: $path"
    return
  fi
  mkdir -p "$(dirname "$path")"
  curl --fail --location --retry 3 --output "$path" "$url"
}

download "$RTMDET_URL" "$MODELS_DIR/rtmdet-nano/$RTMDET_FILE"
download "$RTMPOSE_M_URL" "$MODELS_DIR/rtmpose/$RTMPOSE_M_FILE"
download "$RTMPOSE_S_URL" "$MODELS_DIR/rtmpose/$RTMPOSE_S_FILE"

echo "Official RTMDet-nano and RTMPose M/S checkpoints are ready."
