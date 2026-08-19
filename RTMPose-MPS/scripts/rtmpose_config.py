"""Pinned OpenMMLab RTMDet and RTMPose model locations."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelPaths:
    detector_config: Path
    detector_checkpoint: Path
    pose_config: Path
    pose_checkpoint: Path


_POSE_CHECKPOINTS = {
    "m": "rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth",
    "s": "rtmpose-s_simcc-coco_pt-aic-coco_420e-256x192-8edcf0d7_20230127.pth",
    "halpe26": "rtmpose-m_simcc-body7_pt-body7-halpe26_700e-384x288-89e6428b_20230605.pth",
}


def select_model_paths(root: Path, variant: str) -> ModelPaths:
    """Return paths for the supported RTMPose variants."""
    if variant not in _POSE_CHECKPOINTS:
        raise ValueError("RTMPOSE_VARIANT must be one of: m, s, halpe26")

    pose_config = (
        root
        / "mmpose"
        / "projects"
        / "rtmpose"
        / "rtmpose"
        / "body_2d_keypoint"
        / (
            "rtmpose-m_8xb512-700e_body8-halpe26-384x288.py"
            if variant == "halpe26"
            else f"rtmpose-{variant}_8xb256-420e_coco-256x192.py"
        )
    )

    return ModelPaths(
        detector_config=(
            root
            / "mmpose"
            / "projects"
            / "rtmpose"
            / "rtmdet"
            / "person"
            / "rtmdet_nano_320-8xb32_coco-person.py"
        ),
        detector_checkpoint=(
            root
            / "models"
            / "rtmdet-nano"
            / "rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"
        ),
        pose_config=pose_config,
        pose_checkpoint=root / "models" / "rtmpose" / _POSE_CHECKPOINTS[variant],
    )
