#!/usr/bin/env bash
set -e

echo "HPE 진입"

HPE_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_DIR="$(cd "$HPE_DIR/.." && pwd)"
COACH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Coach 진행 위치 : $COACH_DIR"

## 파이썬 import 경로 지정
export PYTHONPATH="$COACH_DIR"

cd "$COACH_DIR"

RUN_FOLDER="$1"
RUN_DIR="$COACH_DIR/run/$RUN_FOLDER"

OUTPUT_DIR="$RUN_DIR/outputs"

# 테스트 폴더와 inputs, outputs 폴더 생성
mkdir -p "$OUTPUT_DIR"

shift

## mp4 탐지 코드
VIDEO_PATH=$(find "$RUN_DIR" \
    -maxdepth 1 \
    -type f \
    -iname "*.mp4" \
    -print \
    -quit)

if [[ -z "$VIDEO_PATH" ]]; then
    echo "MP4 파일을 찾지 못했습니다: $RUN_DIR"
    exit 1
fi

echo "영상 발견: $VIDEO_PATH"

# ## 스크립트 실행
# "$COACH_DIR/.venv/bin/python" \
#     "$HPE_DIR/extract_frames.py" \
#     "$VIDEO_PATH" \
#     "$RUN_DIR/inputs"

# shift


## HPE 추론
printf '\nHPE 추론\n'
"$COACH_DIR/.venv/bin/python" \
  "$HPE_DIR/hpe.py" \
  "$COACH_DIR" \
  "$RUN_FOLDER" \
  "$VIDEO_PATH" \
  "$@"
