from scripts.rtmw_infer import model_keypoints_to_image, prepare_rtmw_inputs


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


def test_prepare_rtmw_inputs_overrides_incorrect_hugging_face_processor_size():
    """The published processor's 256x192 default must not reach the 384x288 model."""
    inputs = prepare_rtmw_inputs(ShapeProcessor(), object())

    assert inputs["pixel_values"] == (1, 3, 288, 384)


def test_model_keypoints_are_restored_from_rtmw_model_space_to_image_space():
    """RTMW's 384x288 coordinates must land inside the detected person bbox."""
    keypoints = [[0.0, 0.0], [384.0, 288.0], [192.0, 144.0]]

    restored = model_keypoints_to_image(keypoints, [100.0, 50.0, 300.0, 194.0])

    assert restored == [[100.0, 50.0], [300.0, 194.0], [200.0, 122.0]]
