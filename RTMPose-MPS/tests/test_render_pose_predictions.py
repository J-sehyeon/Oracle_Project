import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from scripts.render_pose_predictions import (
    draw_person,
    render_predictions,
    select_draw_points,
)


def _person() -> dict:
    return {
        "track_id": 0,
        "bbox": [0, 0, 63, 63],
        "bbox_score": 0.9,
        "keypoints": [[10, 20], [30, 40]] + [[0, 0]] * 15,
        "keypoint_scores": [0.9, 0.1] + [0.0] * 15,
        "observed": [True, False] + [False] * 15,
        "imputed_keypoints": [None, [35, 45]] + [None] * 15,
    }


def _write_predictions(tmp_path: Path, image_name: str) -> Path:
    json_path = tmp_path / "pose_predictions.json"
    json_path.write_text(
        json.dumps(
            {
                "model": {"keypoints": 17},
                "frames": [{"image_path": image_name, "people": [_person()]}],
            }
        ),
        encoding="utf-8",
    )
    return json_path


def test_select_draw_points_prefers_observed_and_falls_back_to_imputed():
    points = select_draw_points(_person())

    assert points[0] == ((10, 20), "observed")
    assert points[1] == ((35, 45), "imputed")
    assert points[2:] == [None] * 15


def test_draw_person_uses_distinct_observed_and_imputed_colors():
    image = np.zeros((64, 64, 3), dtype=np.uint8)

    draw_person(image, _person())

    assert image[20, 10].tolist() == [0, 255, 0]
    assert image[45, 35].tolist() == [0, 165, 255]


def test_draw_person_connects_coco_ear_to_shoulder():
    person = _person()
    person["keypoints"] = [[0, 0]] * 17
    person["keypoint_scores"] = [0.0] * 17
    person["observed"] = [False] * 17
    person["imputed_keypoints"] = [None] * 17
    person["keypoints"][3] = [20, 20]
    person["keypoints"][5] = [80, 80]
    person["keypoint_scores"][3] = person["keypoint_scores"][5] = 0.9
    person["observed"][3] = person["observed"][5] = True
    image = np.zeros((100, 100, 3), dtype=np.uint8)

    draw_person(image, person)

    assert np.any(image[50, 50] != 0)


def test_draw_person_connects_left_ankle_to_wholebody_foot_keypoints():
    """COCO-WholeBody adds big toe, small toe, and heel after the 17 body points."""
    person = _person()
    person["keypoints"] = [[0, 0]] * 23
    person["keypoint_scores"] = [0.0] * 23
    person["observed"] = [False] * 23
    person["imputed_keypoints"] = [None] * 23
    person["keypoints"][15] = [20, 20]  # left ankle
    person["keypoints"][17] = [80, 80]  # left big toe
    person["keypoint_scores"][15] = person["keypoint_scores"][17] = 0.9
    person["observed"][15] = person["observed"][17] = True
    image = np.zeros((100, 100, 3), dtype=np.uint8)

    draw_person(image, person)

    assert np.any(image[50, 50] != 0)


def test_draw_person_does_not_connect_nose_directly_to_shoulder():
    person = _person()
    person["keypoints"] = [[0, 0]] * 17
    person["keypoint_scores"] = [0.0] * 17
    person["observed"] = [False] * 17
    person["imputed_keypoints"] = [None] * 17
    person["keypoints"][0] = [20, 80]
    person["keypoints"][5] = [80, 20]
    person["keypoint_scores"][0] = person["keypoint_scores"][5] = 0.9
    person["observed"][0] = person["observed"][5] = True
    image = np.zeros((100, 100, 3), dtype=np.uint8)

    draw_person(image, person)

    assert image[50, 50].tolist() == [0, 0, 0]


def test_select_draw_points_rejects_non_numeric_observed_score():
    person = _person()
    person["keypoint_scores"][0] = None
    person["imputed_keypoints"][0] = [12, 22]

    points = select_draw_points(person)

    assert points[0] == ((12, 22), "imputed")


def test_render_predictions_writes_same_name_and_dimensions(tmp_path: Path):
    image_dir = tmp_path / "images"
    output_dir = tmp_path / "rendered"
    image_dir.mkdir()
    source = np.zeros((48, 64, 3), dtype=np.uint8)
    assert cv2.imwrite(str(image_dir / "frame.png"), source)
    json_path = _write_predictions(tmp_path, "frame.png")

    count = render_predictions(json_path, image_dir, output_dir)

    rendered = cv2.imread(str(output_dir / "frame.png"))
    assert count == 1
    assert rendered is not None
    assert rendered.shape == source.shape
    assert np.any(rendered != source)


def test_render_predictions_names_missing_source_image(tmp_path: Path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    json_path = _write_predictions(tmp_path, "missing.png")

    with pytest.raises(FileNotFoundError, match="missing.png"):
        render_predictions(json_path, image_dir, tmp_path / "rendered")


def test_render_predictions_rejects_non_object_json_root(tmp_path: Path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    json_path = tmp_path / "pose_predictions.json"
    json_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="frames array"):
        render_predictions(json_path, image_dir, tmp_path / "rendered")
