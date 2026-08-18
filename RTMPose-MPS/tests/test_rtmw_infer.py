import math

import pytest

from scripts.rtmw_infer import (
    _predict_person,
    prepare_rtmw_inputs,
    repair_rtmw_runtime_buffers,
    serialize_predictions,
)


class ShapeProcessor:
    """Small processor double that exposes the requested output dimensions."""

    def __call__(self, *, images, size=None, return_tensors=None):
        selected = size or {"height": 256, "width": 192}
        return {
            "pixel_values": (
                1,
                3,
                selected["height"],
                selected["width"],
            )
        }


class FillBuffer:
    def __init__(self, value):
        self.value = value

    def fill_(self, value):
        self.value = value


class DeviceValue:
    def to(self, device):
        return self


class OutputValue:
    def __init__(self, value):
        self.value = value

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.value


def test_repair_rtmw_runtime_buffers_restores_nonzero_attention_scale():
    gau = type("Gau", (), {"s": 128, "sqrt_s": FillBuffer(0.0)})()
    model = type("Model", (), {"head": type("Head", (), {"gau": gau})()})()

    repair_rtmw_runtime_buffers(model)

    assert gau.sqrt_s.value == pytest.approx(math.sqrt(128))


def test_serialize_predictions_rejects_nonfinite_scores():
    payload = {"frames": [{"people": [{"keypoint_scores": [math.nan]}]}]}

    with pytest.raises(ValueError, match="JSON-compliant"):
        serialize_predictions(payload)


def test_prepare_rtmw_inputs_overrides_incorrect_hugging_face_processor_size():
    """The published processor's 256x192 default must not reach the 384x288 model."""
    inputs = prepare_rtmw_inputs(ShapeProcessor(), object())

    assert inputs["pixel_values"] == (1, 3, 384, 288)


def test_predict_person_asks_model_for_original_image_coordinates():
    class Image:
        def crop(self, bbox):
            return object()

    class Processor:
        def __call__(self, **kwargs):
            return {"pixel_values": DeviceValue()}

    class PoseModel:
        def __call__(self, **kwargs):
            self.kwargs = kwargs
            return type(
                "Outputs",
                (),
                {
                    "keypoints": [OutputValue([[123.0, 456.0]])],
                    "scores": [OutputValue([0.9])],
                },
            )()

    class Torch:
        class no_grad:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

    model = PoseModel()
    bbox = [100.0, 50.0, 300.0, 450.0]

    keypoints, scores = _predict_person(
        Image(), bbox, Processor(), model, Torch, "cpu"
    )

    assert model.kwargs["coordinate_mode"] == "image"
    assert model.kwargs["bbox"] == bbox
    assert keypoints == [[123.0, 456.0]]
    assert scores == [0.9]
