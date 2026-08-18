#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_PATH="$ROOT_DIR/models/rtmdet-nano/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"
MODEL_URL="https://download.openmmlab.com/mmpose/v1/projects/rtmpose/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "RTMDet-nano: $MODEL_URL"
  echo "RTMW-X: downloaded from Hugging Face on first inference (akore/rtmw-x-384x288)"
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

if [[ -f "$MODEL_PATH" ]]; then
  echo "Already present: $MODEL_PATH"
  exit 0
fi

mkdir -p "$(dirname "$MODEL_PATH")"
curl --fail --location --retry 3 --output "$MODEL_PATH" "$MODEL_URL"
echo "RTMDet-nano checkpoint is ready. RTMW-X downloads on its first inference."
