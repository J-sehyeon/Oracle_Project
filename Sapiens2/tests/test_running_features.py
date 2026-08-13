import math

import pytest

from scripts.running_features import (
    angle_degrees,
    analyze_pose_json,
    body_reference,
    load_pose_frames,
)


NAMES = [
    "right_eye", "right_ear", "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow", "left_wrist", "right_wrist",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_toe", "right_toe",
    "left_heel", "right_heel",
]


def make_frame(index, left_foot_y, right_foot_y):
    points = {
        "left_shoulder": (0, 0), "right_shoulder": (2, 0),
        "left_hip": (0, 10), "right_hip": (2, 10),
        "left_knee": (0, 20), "right_knee": (2, 20),
        "left_ankle": (0, 30), "right_ankle": (2, 30),
        "left_toe": (3, left_foot_y), "right_toe": (5, right_foot_y),
        "left_heel": (-2, left_foot_y), "right_heel": (1, right_foot_y),
    }
    return {
        "image_name": f"{index:08d}.png",
        "instances": [{
            "keypoints": [points.get(name, (0, 0)) for name in NAMES],
            "keypoint_scores": [1.0] * len(NAMES),
        }],
    }


def synthetic_running_payload():
    # Left and right feet alternately reach their lowest screen position.
    left = [30, 34, 40, 34, 30, 34, 40, 34, 30, 34, 40, 34]
    right = [40, 34, 30, 34, 40, 34, 30, 34, 40, 34, 30, 34]
    return {
        "format": "sapiens2_body18_v1",
        "keypoint_names": NAMES,
        "frames": [make_frame(i, left[i], right[i]) for i in range(len(left))],
    }


def test_joint_angle_returns_the_angle_at_the_middle_point():
    assert angle_degrees((1, 0), (0, 0), (0, 1)) == pytest.approx(90)


def test_body_reference_uses_median_torso_and_average_leg_length():
    frames = load_pose_frames(synthetic_running_payload(), threshold=0.3)

    # torso=10; each leg=20, so the body reference is 30 pixels.
    assert body_reference(frames) == pytest.approx(30)


def test_analysis_returns_normalized_features_and_unavailable_vlr():
    result = analyze_pose_json(synthetic_running_payload(), fps=25)

    assert result["body_reference_px"] == pytest.approx(30)
    # Alternating left/right contacts occur every two frames: 60 * 25 / 2.
    assert result["features"]["FEAT-03"]["value"] == pytest.approx(750)
    assert result["features"]["FEAT-06"]["unit"] == "% body_reference"
    assert result["features"]["FEAT-12"]["value"] is None
    assert "force" in result["features"]["FEAT-12"]["reason"].lower()


def test_height_adds_estimated_centimetres_without_changing_normalized_value():
    result = analyze_pose_json(synthetic_running_payload(), fps=25, height_cm=180)

    overstride = result["features"]["FEAT-08"]
    assert overstride["estimated_cm"] == pytest.approx(overstride["value"] * 1.8)
