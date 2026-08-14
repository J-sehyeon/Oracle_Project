from scripts.pose_track import Detection, TrackState, build_frame_record


def detection_with_scores(scores: list[float]) -> Detection:
    return Detection(
        bbox=[10.0, 20.0, 50.0, 80.0],
        bbox_score=0.9,
        keypoints=[[10.0, 20.0] for _ in range(17)],
        keypoint_scores=scores,
    )


def previous_state() -> TrackState:
    return TrackState(
        bbox=[9.0, 19.0, 49.0, 79.0],
        keypoints=[[1.0, 2.0] for _ in range(17)],
    )


def test_low_confidence_point_stays_raw_and_gets_separate_imputation():
    """Overwriting raw coordinates with an imputed point must fail this test."""
    record, state = build_frame_record(
        "0002.png", [detection_with_scores([0.9] * 16 + [0.1])], previous_state(), 0.3
    )

    person = record["people"][0]
    assert person["track_id"] == 0
    assert person["observed"][-1] is False
    assert person["keypoints"][-1] == [10.0, 20.0]
    assert person["imputed_keypoints"][-1] == [1.0, 2.0]
    assert state is not None


def test_empty_detection_preserves_empty_people_array():
    """Dropping no-detection frames would break frame alignment."""
    record, state = build_frame_record("0003.png", [], None, 0.3)

    assert record == {"image_path": "0003.png", "people": []}
    assert state is None


def test_primary_track_prefers_highest_iou_over_detector_score():
    """Selecting only by score would switch identities during overlap."""
    nearby = Detection(
        bbox=[11.0, 21.0, 51.0, 81.0],
        bbox_score=0.6,
        keypoints=[[11.0, 21.0] for _ in range(17)],
        keypoint_scores=[0.9] * 17,
    )
    distant = Detection(
        bbox=[100.0, 100.0, 160.0, 180.0],
        bbox_score=0.99,
        keypoints=[[100.0, 100.0] for _ in range(17)],
        keypoint_scores=[0.9] * 17,
    )

    _, state = build_frame_record("0004.png", [distant, nearby], previous_state(), 0.3)

    assert state is not None
    assert state.bbox == nearby.bbox
