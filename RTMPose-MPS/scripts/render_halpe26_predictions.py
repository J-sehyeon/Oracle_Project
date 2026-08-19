"""Draw Halpe-26 pose predictions on their original images."""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

try:
    from scripts.render_pose_predictions import (
        IMPUTED_COLOR,
        OBSERVED_COLOR,
        select_draw_points,
    )
except ModuleNotFoundError:
    from render_pose_predictions import (
        IMPUTED_COLOR,
        OBSERVED_COLOR,
        select_draw_points,
    )


HALPE26_SKELETON = (
    (15, 13), (13, 11), (11, 19),
    (16, 14), (14, 12), (12, 19),
    (17, 18), (18, 19),
    (18, 5), (5, 7), (7, 9),
    (18, 6), (6, 8), (8, 10),
    (1, 2), (0, 1), (0, 2), (1, 3), (2, 4),
    (3, 5), (4, 6),
    (15, 20), (15, 22), (15, 24),
    (16, 21), (16, 23), (16, 25),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions_json", type=Path)
    parser.add_argument("image_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    return parser.parse_args()


def draw_person(image: np.ndarray, person: dict) -> None:
    """Draw one Halpe-26 skeleton and its observed or imputed keypoints."""
    points = select_draw_points(person)
    if len(points) != 26:
        raise ValueError("Each Halpe-26 person must contain exactly 26 keypoints")

    for start_index, end_index in HALPE26_SKELETON:
        start = points[start_index]
        end = points[end_index]
        if start is None or end is None:
            continue
        color = OBSERVED_COLOR if start[1] == end[1] == "observed" else IMPUTED_COLOR
        cv2.line(image, start[0], end[0], color, 2, cv2.LINE_AA)

    for point in points:
        if point is None:
            continue
        color = OBSERVED_COLOR if point[1] == "observed" else IMPUTED_COLOR
        cv2.circle(image, point[0], 3, color, -1, cv2.LINE_AA)


def render_predictions(json_path: Path, image_dir: Path, output_dir: Path) -> int:
    """Render all frames in a Halpe-26 predictions JSON file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"Predictions JSON does not exist: {json_path}")
    if not image_dir.is_dir():
        raise NotADirectoryError(f"Image directory does not exist: {image_dir}")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("frames"), list):
        raise ValueError("Pose predictions JSON must contain a frames array")
    model = payload.get("model")
    if not isinstance(model, dict) or model.get("keypoints") != 26:
        raise ValueError("Halpe-26 renderer requires predictions with 26 keypoints")

    output_dir.mkdir(parents=True, exist_ok=True)
    for frame in payload["frames"]:
        image_name = Path(frame["image_path"]).name
        source = image_dir / image_name
        if not source.is_file():
            raise FileNotFoundError(f"Source image does not exist: {source}")
        image = cv2.imread(str(source))
        if image is None:
            raise ValueError(f"Failed to read source image: {source}")
        for person in frame.get("people", []):
            draw_person(image, person)
        destination = output_dir / image_name
        if not cv2.imwrite(str(destination), image):
            raise OSError(f"Failed to write output image: {destination}")
    return len(payload["frames"])


def main() -> None:
    args = parse_args()
    try:
        count = render_predictions(args.predictions_json, args.image_dir, args.output_dir)
    except (KeyError, OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print(f"Images rendered: {count}")
    print(f"Output directory: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
