import time
import argparse
from pathlib import Path

import cv2


def extract_frames(video_path: Path, output_dir: Path) -> int:
    if output_dir.exists() and any(output_dir.glob("*.png")):
        print(f"기존 프레임이 있습니다: {output_dir}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    video = cv2.VideoCapture(str(video_path))
    if not video.isOpened():
        raise RuntimeError(f"영상을 열지 못했습니다: {video_path}")

    count = 0

    try:
        while True:
            success, frame = video.read()
            if not success:
                break

            count += 1
            cv2.imwrite(str(output_dir / f"{count:08d}.png"), frame)
    finally:
        video.release()

    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    start = time.perf_counter()
    count = extract_frames(args.video, args.output)
    end = time.perf_counter()

    print(f"{count}개 프레임 저장 완료: {args.output}  |  지연 시간: {end - start:.2f}s")
