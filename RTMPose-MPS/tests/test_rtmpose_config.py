from pathlib import Path

import pytest

from scripts.rtmpose_config import select_model_paths


def test_m_variant_selects_coco17_rtmpose_m_checkpoint(tmp_path: Path):
    """Changing the default model away from M/COCO-17 must fail this test."""
    paths = select_model_paths(tmp_path, "m")

    assert paths.pose_checkpoint.name == (
        "rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth"
    )
    assert paths.pose_config.name == "rtmpose-m_8xb256-420e_coco-256x192.py"
    assert paths.detector_checkpoint.name == (
        "rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"
    )


def test_s_variant_selects_optional_smaller_coco17_checkpoint(tmp_path: Path):
    """Breaking the documented S fallback must fail this test."""
    paths = select_model_paths(tmp_path, "s")

    assert paths.pose_checkpoint.name == (
        "rtmpose-s_simcc-coco_pt-aic-coco_420e-256x192-8edcf0d7_20230127.pth"
    )


def test_unknown_variant_is_rejected(tmp_path: Path):
    """Accepting an unsupported variant would silently change the quality contract."""
    with pytest.raises(ValueError, match="RTMPOSE_VARIANT"):
        select_model_paths(tmp_path, "l")
