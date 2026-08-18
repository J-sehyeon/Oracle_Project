from scripts.rtmw_infer import model_keypoints_to_image


def test_model_keypoints_are_restored_from_rtmw_model_space_to_image_space():
    """RTMW's 384x288 coordinates must land inside the detected person bbox."""
    keypoints = [[0.0, 0.0], [384.0, 288.0], [192.0, 144.0]]

    restored = model_keypoints_to_image(keypoints, [100.0, 50.0, 300.0, 194.0])

    assert restored == [[100.0, 50.0], [300.0, 194.0], [200.0, 122.0]]
