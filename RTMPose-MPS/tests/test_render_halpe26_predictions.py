import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import cv2
import numpy as np
import pytest

import scripts.render_halpe26_predictions as halpe_renderer


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_halpe26_predictions.py"


def test_halpe26_renderer_is_available_as_a_dedicated_script():
    """Halpe output needs a distinct 26-keypoint renderer, not the RTMW renderer."""
    assert importlib.util.find_spec("scripts.render_halpe26_predictions") is not None


def test_halpe26_renderer_can_run_directly_as_documented():
    """The README invocation must work without requiring Python's module mode."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def _halpe_person() -> dict:
    return {
        "keypoints": [[0, 0] for _ in range(26)],
        "keypoint_scores": [0.0] * 26,
        "observed": [False] * 26,
        "imputed_keypoints": [None] * 26,
    }


def test_draw_person_connects_halpe_neck_to_pelvis_and_ankle_to_heel():
    person = _halpe_person()
    for index, point in ((18, [20, 20]), (19, [80, 20]), (15, [20, 80]), (24, [80, 80])):
        person["keypoints"][index] = point
        person["keypoint_scores"][index] = 0.9
        person["observed"][index] = True
    image = np.zeros((100, 100, 3), dtype=np.uint8)

    halpe_renderer.draw_person(image, person)

    assert np.any(image[20, 50] != 0)
    assert np.any(image[80, 50] != 0)


def test_render_predictions_rejects_non_halpe26_model_metadata(tmp_path: Path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    assert cv2.imwrite(str(image_dir / "frame.png"), np.zeros((10, 10, 3), dtype=np.uint8))
    predictions = tmp_path / "pose_predictions.json"
    predictions.write_text(
        json.dumps({"model": {"keypoints": 17}, "frames": []}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Halpe-26"):
        halpe_renderer.render_predictions(predictions, image_dir, tmp_path / "rendered")
