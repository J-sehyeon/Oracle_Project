#!/usr/bin/env bash
set -e

echo "Rendering 진입"

RENDER_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_DIR="$(cd "$RENDER_DIR/.." && pwd)"
COACH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Coach 진행 위치 : $COACH_DIR"

## 파이썬 import 경로 지정
export PYTHONPATH="$COACH_DIR"

cd "$COACH_DIR"

RUN_FOLDER="$1"
RUN_DIR="$COACH_DIR/run/$RUN_FOLDER"

INPUT_DIR="$RUN_DIR/inputs"
OUTPUT_DIR="$RUN_DIR/outputs"

# 테스트 폴더와 inputs, outputs 폴더 생성
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

shift

## 렌더링
printf '\n렌더링\n'
"$COACH_DIR/.venv/bin/python" \
  "$RENDER_DIR/render.py" \
  "$INPUT_DIR" \
  "$OUTPUT_DIR"

## 렌더링 이미지로 영상 합성
printf '\n이미지 합성\n'
"$COACH_DIR/.venv/bin/python" \
  "$RENDER_DIR/compose_video.py" \
  "$OUTPUT_DIR/details.json" \
  "$OUTPUT_DIR/rendered" \
  "$OUTPUT_DIR/_rendered.mp4"

ffmpeg \
  -hide_banner \
  -loglevel error \
  -stats \
  -i "$OUTPUT_DIR/_rendered.mp4" \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$OUTPUT_DIR/rendered.mp4"