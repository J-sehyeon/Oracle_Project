#!/usr/bin/env bash
set -e

echo "HPE 진입"

HPE_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_DIR="$(cd "$HPE_DIR/.." && pwd)"
POC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "PoC 진행 위치 : $POC_DIR"

## 파이썬 import 경로 지정
export PYTHONPATH="$POC_DIR"

cd "$POC_DIR"

RUN_FOLDER="$1"
RUN_DIR="$POC_DIR/run/$RUN_FOLDER"

INPUT_DIR="$RUN_DIR/inputs"
OUTPUT_DIR="$RUN_DIR/outputs"

# 테스트 폴더와 inputs, outputs 폴더 생성
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

shift


## 영상에서 이미지 추출 조건
if [[ "${1:-}" == "--extract" ]]; then

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

    ## 스크립트 실행
    "$POC_DIR/.venv/bin/python" \
        "$HPE_DIR/extract_frames.py" \
        "$VIDEO_PATH" \
        "$RUN_DIR/inputs"

    shift
fi

## HPE 추론
printf '\nHPE 추론\n'
"$POC_DIR/.venv/bin/python" \
  "$HPE_DIR/hpe_model.py" \
  "$POC_DIR" \
  "$RUN_FOLDER" \
  "$@"

## 렌더링
printf '\n렌더링\n'
"$POC_DIR/.venv/bin/python" \
  "$HPE_DIR/render.py" \
  "$RUN_DIR/inputs" \
  "$RUN_DIR/outputs"

## 렌더링 이미지로 영상 합성
printf '\n이미지 합성\n'
"$POC_DIR/.venv/bin/python" \
  "$HPE_DIR/compose_video.py" \
  "$RUN_DIR/outputs/details.json" \
  "$RUN_DIR/outputs/rendered" \
  "$RUN_DIR/outputs/_rendered.mp4"

ffmpeg \
  -hide_banner \
  -loglevel error \
  -stats \
  -i "$RUN_DIR/outputs/_rendered.mp4" \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$RUN_DIR/outputs/rendered.mp4"