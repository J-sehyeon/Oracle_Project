from pathlib import Path

import pytest

from scripts.rtmpose_config import select_model_paths
from scripts.rtmpose_infer import (
    install_mps_nms_fallback,
    run_topdown_inference,
    trusted_checkpoint_loading,
)


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


def test_trusted_checkpoint_loading_only_overrides_torch_load_in_context():
    class FakeTorch:
        def __init__(self):
            self.calls = []

        def load(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return "loaded"

    torch = FakeTorch()
    original_load = torch.load.__func__

    with trusted_checkpoint_loading(torch):
        assert torch.load("official.pth") == "loaded"

    assert torch.load.__func__ is original_load
    assert torch.calls == [(("official.pth",), {"weights_only": False})]


def test_topdown_inference_switches_registry_scope_for_each_model():
    class Instances:
        bboxes = [[1, 2, 3, 4]]
        scores = [0.9]
        labels = [0]

        def cpu(self):
            return self

        def numpy(self):
            return self

    class DetectionResult:
        pred_instances = Instances()

    scopes = []
    received_boxes = []

    def set_scope(scope):
        scopes.append(scope)

    def infer_detector(model, image):
        return DetectionResult()

    def infer_pose(model, image, boxes):
        received_boxes.extend(boxes)
        return ["pose"]

    det_result, pose_results = run_topdown_inference(
        "detector", "pose", "frame.jpg", 0.3, set_scope, infer_detector, infer_pose
    )

    assert isinstance(det_result.pred_instances, Instances)
    assert pose_results == ["pose"]
    assert scopes == ["mmdet", "mmpose"]
    assert received_boxes == [[1, 2, 3, 4]]


def test_mps_nms_fallback_keeps_indices_on_cpu_for_mmengine():
    class Tensor:
        def __init__(self, name, device):
            self.name = name
            self.device = type("Device", (), {"type": device})()

        def cpu(self):
            return Tensor(self.name, "cpu")

        def to(self, device):
            return Tensor(self.name, device.type)

    class Module:
        def __init__(self):
            self.calls = []

        def nms(self, boxes, scores, **kwargs):
            self.calls.append((boxes.device.type, scores.device.type, kwargs))
            return Tensor("dets", "cpu"), Tensor("keep", "cpu")

    module = Module()
    install_mps_nms_fallback(module)

    dets, keep = module.nms(Tensor("boxes", "mps"), Tensor("scores", "mps"), iou_threshold=0.7)

    assert module.calls == [("cpu", "cpu", {"iou_threshold": 0.7})]
    assert dets.device.type == "mps"
    assert keep.device.type == "cpu"
