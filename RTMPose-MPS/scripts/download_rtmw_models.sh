#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DETECTOR_PATH="$ROOT_DIR/models/rtmdet-nano/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"
DETECTOR_URL="https://download.openmmlab.com/mmpose/v1/projects/rtmpose/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"
HALPE26_PATH="$ROOT_DIR/models/rtmpose/rtmpose-m_simcc-body7_pt-body7-halpe26_700e-384x288-89e6428b_20230605.pth"
HALPE26_URL="https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-m_simcc-body7_pt-body7-halpe26_700e-384x288-89e6428b_20230605.pth"

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "RTMDet-nano: $DETECTOR_URL"
  echo "RTMW-X: downloaded from Hugging Face on first inference (akore/rtmw-x-384x288)"
  echo "RTMPose-M Halpe-26: $HALPE26_URL"
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

download_if_missing() {
  local path="$1"
  local url="$2"

  if [[ -f "$path" ]]; then
    echo "Already present: $path"
    return
  fi

  mkdir -p "$(dirname "$path")"
  curl --fail --location --retry 3 --output "$path" "$url"
}

download_if_missing "$DETECTOR_PATH" "$DETECTOR_URL"
download_if_missing "$HALPE26_PATH" "$HALPE26_URL"
echo "RTMDet-nano and RTMPose-M Halpe-26 checkpoints are ready. RTMW-X downloads on its first inference."
