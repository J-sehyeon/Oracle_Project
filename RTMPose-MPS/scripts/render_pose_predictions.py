"""Draw pose_predictions.json keypoints on their original images."""

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np


COCO_SKELETON = (
    (15, 13),
    (13, 11),
    (16, 14),
    (14, 12),
    (11, 12),
    (5, 11),
    (6, 12),
    (5, 6),
    (5, 7),
    (6, 8),
    (7, 9),
    (8, 10),
    (1, 2),
    (0, 1),
    (0, 2),
    (1, 3),
    (2, 4),
    (3, 5),
    (4, 6),
)
OBSERVED_COLOR = (0, 255, 0)
IMPUTED_COLOR = (0, 165, 255)
DrawPoint = tuple[tuple[int, int], str] | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions_json", type=Path)
    parser.add_argument("image_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    return parser.parse_args()


def select_draw_points(person: dict) -> list[DrawPoint]:
    """Select observed coordinates, falling back to imputed coordinates."""
    points: list[DrawPoint] = []
    for point, score, observed, imputed in zip(
        person["keypoints"],
        person["keypoint_scores"],
        person["observed"],
        person["imputed_keypoints"],
        strict=True,
    ):
        valid_score = isinstance(score, (int, float)) and math.isfinite(score)
        if observed and valid_score:
            points.append(((round(point[0]), round(point[1])), "observed"))
        elif imputed is not None:
            points.append(((round(imputed[0]), round(imputed[1])), "imputed"))
        else:
            points.append(None)
    return points


def draw_person(image: np.ndarray, person: dict) -> None:
    """Draw one person's COCO-17 skeleton and keypoints in place."""
    points = select_draw_points(person)
    for start_index, end_index in COCO_SKELETON:
        start = points[start_index]
        end = points[end_index]
        if start is None or end is None:
            continue
        color = (
            OBSERVED_COLOR
            if start[1] == end[1] == "observed"
            else IMPUTED_COLOR
        )
        cv2.line(image, start[0], end[0], color, 2, cv2.LINE_AA)

    for point in points:
        if point is None:
            continue
        color = OBSERVED_COLOR if point[1] == "observed" else IMPUTED_COLOR
        cv2.circle(image, point[0], 3, color, -1, cv2.LINE_AA)


def render_predictions(
    json_path: Path, image_dir: Path, output_dir: Path
) -> int:
    """Render every frame in a pose predictions JSON file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"Predictions JSON does not exist: {json_path}")
    if not image_dir.is_dir():
        raise NotADirectoryError(f"Image directory does not exist: {image_dir}")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Pose predictions JSON must contain a frames array")
    frames = payload.get("frames")
    if not isinstance(frames, list):
        raise ValueError("Pose predictions JSON must contain a frames array")

    output_dir.mkdir(parents=True, exist_ok=True)
    for frame in frames:
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

    return len(frames)


def main() -> None:
    args = parse_args()
    try:
        count = render_predictions(
            args.predictions_json, args.image_dir, args.output_dir
        )
    except (KeyError, OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print(f"Images rendered: {count}")
    print(f"Output directory: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
