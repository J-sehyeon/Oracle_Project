import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


FEATURE_NAMES = (
    "postural_lean_deg",
    "torso_flexion_deg",
    "lean_variability_deg",
    "pelvis_to_ankle_ap_distance",
    "peak_knee_flexion_stance_deg",
    "tibia_angle_deg",
    "hip_extension_late_stance_deg",
    "heel_to_com_ap_distance",
    "overstride_asymmetry_pct",
    "knee_flexion_at_ic_deg",
    "max_knee_flexion_stance_deg",
    "knee_flexion_excursion_deg",
    "foot_inclination_at_ic_deg",
    "cadence_spm",
    "step_time_asymmetry_pct",
    "estimated_stance_time_asymmetry_pct",
    "knee_rom_asymmetry_pct",
    "elbow_angle_rom_deg",
)


@dataclass
class PoseSequence:
    coordinates_px: np.ndarray
    coordinates: np.ndarray
    scores: np.ndarray
    observed: np.ndarray
    bboxes: np.ndarray
    frame_numbers: np.ndarray
    image_paths: tuple[str, ...]
    stature_px: np.ndarray
    user_height_m: float


@dataclass(frozen=True)
class GaitEvents:
    contacts: dict[str, np.ndarray]
    stance_intervals: dict[str, tuple[tuple[int, int], ...]]


def load_pose_sequence(json_path: str | Path, user_height_m: float) -> PoseSequence:
    """Load track 0 and normalize each frame around the pelvis center."""
    if user_height_m <= 0:
        raise ValueError("user_height_m must be positive")

    path = Path(json_path)
    with path.open(encoding="utf-8") as file:
        frames = json.load(file)["frames"]

    frame_count = len(frames)
    coordinates = np.full((frame_count, 26, 2), np.nan, dtype=float)
    scores = np.full((frame_count, 26), np.nan, dtype=float)
    observed = np.zeros((frame_count, 26), dtype=bool)
    bboxes = np.full((frame_count, 4), np.nan, dtype=float)
    image_paths = []

    for frame_index, frame in enumerate(frames):
        image_paths.append(str(frame.get("image_path", "")))
        person = next(
            (item for item in frame.get("people", ()) if item.get("track_id") == 0),
            None,
        )
        if person is None:
            continue

        raw = np.asarray(person["keypoints"], dtype=float)
        if raw.shape != (26, 2):
            raise ValueError(f"frame {frame_index}: expected 26 Halpe keypoints")
        frame_observed = np.asarray(person["observed"], dtype=bool)
        frame_scores = np.asarray(person["keypoint_scores"], dtype=float)
        if frame_observed.shape != (26,) or frame_scores.shape != (26,):
            raise ValueError(f"frame {frame_index}: invalid keypoint metadata")

        selected = raw.copy()
        for keypoint_index, imputed in enumerate(person["imputed_keypoints"]):
            if not frame_observed[keypoint_index]:
                selected[keypoint_index] = (
                    np.asarray(imputed, dtype=float) if imputed is not None else np.nan
                )

        coordinates[frame_index] = selected
        scores[frame_index] = frame_scores
        observed[frame_index] = frame_observed
        bboxes[frame_index] = np.asarray(person["bbox"], dtype=float)

    pelvis = _pelvis_center(coordinates)
    stature_px = _estimate_stature_px(coordinates, pelvis, bboxes)
    normalized = (coordinates - pelvis[:, None, :]) / stature_px[:, None, None]

    return PoseSequence(
        coordinates_px=coordinates,
        coordinates=normalized,
        scores=scores,
        observed=observed,
        bboxes=bboxes,
        frame_numbers=np.arange(frame_count),
        image_paths=tuple(image_paths),
        stature_px=stature_px,
        user_height_m=float(user_height_m),
    )


def load_run_metadata(
    run_dir: str | Path,
    user_height_m: float | None = None,
) -> tuple[float, float]:
    """Return (runner height in metres, video FPS) from run metadata."""
    root = Path(run_dir)
    candidates = (
        root / "outputs" / "details.json",
        root / "details.json",
        root / "metadata.json",
        root / "user.json",
        root / "profile.json",
    )
    height_m = user_height_m
    fps = None

    for path in candidates:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        if height_m is None:
            height_m = _height_from_metadata(data)
        if fps is None:
            video = data.get("video", {}) if isinstance(data, dict) else {}
            value = video.get("fps", data.get("fps") if isinstance(data, dict) else None)
            if value is not None:
                fps = float(value)

    if height_m is None:
        raise ValueError("runner height not found (supported keys: height_m or height_cm)")
    if fps is None or fps <= 0:
        raise ValueError("positive video fps not found")
    return height_m, fps


def extract_features_from_run(
    run_dir: str | Path,
    direction: int | None = None,
    user_height_m: float | None = None,
) -> dict[str, float]:
    """Load one run directory and calculate all PDF features."""
    root = Path(run_dir)
    height_m, fps = load_run_metadata(root, user_height_m=user_height_m)
    sequence = load_pose_sequence(
        root / "outputs" / "pose_predictions.json",
        user_height_m=height_m,
    )
    return calculate_features(sequence, fps=fps, direction=direction)


def detect_gait_events(
    sequence: PoseSequence,
    fps: float,
    min_step_seconds: float = 0.18,
) -> GaitEvents:
    """Detect foot contacts as well-separated local maxima of foot height."""
    if fps <= 0:
        raise ValueError("fps must be positive")
    # Consecutive contacts of the same foot span two alternating steps.
    minimum_distance = max(1, int(round(fps * min_step_seconds * 2)))
    contacts = {}
    intervals = {}

    for side in ("left", "right"):
        indices = _side_indices(side)
        signal = _nanmean(sequence.coordinates[:, indices["foot"], 1], axis=1)
        signal = _interpolate(signal)
        smoothed = np.convolve(
            np.pad(signal, 1, mode="edge"),
            np.ones(3) / 3,
            mode="valid",
        )
        baseline = float(np.nanmedian(smoothed))
        amplitude = float(np.nanmax(smoothed) - np.nanmin(smoothed))
        if amplitude <= np.finfo(float).eps:
            contacts[side] = np.empty(0, dtype=int)
            intervals[side] = ()
            continue
        threshold = baseline + 0.5 * (float(np.nanmax(smoothed)) - baseline)
        candidates = np.flatnonzero(
            (smoothed[1:-1] > smoothed[:-2])
            & (smoothed[1:-1] >= smoothed[2:])
            & (smoothed[1:-1] >= threshold)
        ) + 1
        selected = _separate_peaks(candidates, smoothed, minimum_distance)
        contacts[side] = selected
        intervals[side] = _stance_intervals(selected, smoothed, baseline)

    return GaitEvents(contacts=contacts, stance_intervals=intervals)


def calculate_features(
    sequence: PoseSequence,
    fps: float,
    events: GaitEvents | None = None,
    direction: int | None = None,
) -> dict[str, float]:
    """Calculate the PDF feature set and return one aggregate value per feature."""
    if fps <= 0:
        raise ValueError("fps must be positive")
    if events is None:
        events = detect_gait_events(sequence, fps)
    if direction is None:
        direction = _running_direction(sequence)
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 (left) or 1 (right)")

    points = sequence.coordinates
    shoulder = _nanmean(points[:, [5, 6]], axis=1)
    pelvis = _nanmean(points[:, [11, 12]], axis=1)
    all_contacts = _ordered_contacts(events)

    lean_values = []
    torso_values = []
    pelvis_ankle = {"left": [], "right": []}
    heel_com = {"left": [], "right": []}
    knee_ic = []
    tibia_ic = []
    foot_ic = []

    for frame, side in all_contacts:
        idx = _side_indices(side)
        ankle = points[frame, idx["ankle"]]
        lean_values.append(
            np.degrees(
                np.arctan2(
                    direction * (shoulder[frame, 0] - ankle[0]),
                    ankle[1] - shoulder[frame, 1],
                )
            )
        )
        torso_values.append(
            np.degrees(
                np.arctan2(
                    direction * (shoulder[frame, 0] - pelvis[frame, 0]),
                    pelvis[frame, 1] - shoulder[frame, 1],
                )
            )
        )
        pelvis_ankle[side].append(
            abs(ankle[0] - pelvis[frame, 0]) * sequence.user_height_m
        )
        heel = points[frame, idx["heel"]]
        heel_com[side].append(
            abs(heel[0] - pelvis[frame, 0]) * sequence.user_height_m
        )
        knee_ic.append(_knee_flexion(points[frame], idx))
        tibia_ic.append(_tibia_angle(points[frame], idx, direction))
        foot_ic.append(_foot_angle(points[frame], idx))

    stance_peaks = []
    excursions = []
    hip_extensions = []
    stance_seconds = {"left": [], "right": []}
    for side in ("left", "right"):
        idx = _side_indices(side)
        side_contacts = events.contacts[side]
        for interval_index, (start, end) in enumerate(events.stance_intervals[side]):
            flexion = np.array(
                [_knee_flexion(points[frame], idx) for frame in range(start, end + 1)]
            )
            peak = _safe_max(flexion)
            stance_peaks.append(peak)
            if interval_index < len(side_contacts):
                ic_flexion = _knee_flexion(points[side_contacts[interval_index]], idx)
                excursions.append(peak - ic_flexion)
            late_start = start + (2 * (end - start) // 3)
            hip_extensions.append(
                _safe_max(
                    np.array(
                        [
                            _hip_extension(points[frame], idx)
                            for frame in range(late_start, end + 1)
                        ]
                    )
                )
            )
            stance_seconds[side].append((end - start + 1) / fps)

    side_step_times = {"left": [], "right": []}
    for (previous_frame, previous_side), (frame, side) in zip(
        all_contacts, all_contacts[1:]
    ):
        if side != previous_side:
            side_step_times[side].append((frame - previous_frame) / fps)

    knee_rom = {}
    elbow_rom = []
    for side in ("left", "right"):
        idx = _side_indices(side)
        cycle_rom = []
        for start, end in zip(events.contacts[side], events.contacts[side][1:]):
            flexion = np.array(
                [_knee_flexion(points[frame], idx) for frame in range(start, end + 1)]
            )
            cycle_rom.append(_safe_range(flexion))
        knee_rom[side] = _safe_mean(cycle_rom, default=0.0)
        elbow_angles = np.array(
            [_elbow_flexion(frame_points, idx) for frame_points in points]
        )
        elbow_rom.append(_safe_range(elbow_angles))

    duration_seconds = len(points) / fps
    cadence = (
        len(all_contacts) * 60.0 / duration_seconds
        if duration_seconds > 0
        else float("nan")
    )
    peak_knee = _safe_mean(stance_peaks)

    values = {
        "postural_lean_deg": _safe_mean(lean_values),
        "torso_flexion_deg": _safe_mean(torso_values),
        "lean_variability_deg": _safe_std(lean_values),
        "pelvis_to_ankle_ap_distance": _safe_mean(
            pelvis_ankle["left"] + pelvis_ankle["right"]
        ),
        "peak_knee_flexion_stance_deg": peak_knee,
        "tibia_angle_deg": _safe_mean(tibia_ic),
        "hip_extension_late_stance_deg": _safe_mean(hip_extensions),
        "heel_to_com_ap_distance": _safe_mean(
            heel_com["left"] + heel_com["right"]
        ),
        "overstride_asymmetry_pct": _asymmetry(
            _safe_mean(pelvis_ankle["left"]),
            _safe_mean(pelvis_ankle["right"]),
        ),
        "knee_flexion_at_ic_deg": _safe_mean(knee_ic),
        "max_knee_flexion_stance_deg": peak_knee,
        "knee_flexion_excursion_deg": _safe_mean(excursions),
        "foot_inclination_at_ic_deg": _safe_mean(foot_ic),
        "cadence_spm": cadence,
        "step_time_asymmetry_pct": _asymmetry(
            _safe_mean(side_step_times["left"]),
            _safe_mean(side_step_times["right"]),
        ),
        "estimated_stance_time_asymmetry_pct": _asymmetry(
            _safe_mean(stance_seconds["left"]),
            _safe_mean(stance_seconds["right"]),
        ),
        "knee_rom_asymmetry_pct": _asymmetry(knee_rom["left"], knee_rom["right"]),
        "elbow_angle_rom_deg": _safe_mean(elbow_rom),
    }
    return {name: float(values[name]) for name in FEATURE_NAMES}


def _pelvis_center(coordinates: np.ndarray) -> np.ndarray:
    pelvis = _nanmean(coordinates[:, [11, 12]], axis=1)
    missing = ~np.isfinite(pelvis).all(axis=1)
    pelvis[missing] = coordinates[missing, 19]
    return pelvis


def _estimate_stature_px(
    coordinates: np.ndarray,
    pelvis: np.ndarray,
    bboxes: np.ndarray,
) -> np.ndarray:
    head_neck = np.linalg.norm(coordinates[:, 17] - coordinates[:, 18], axis=1)
    neck_pelvis = np.linalg.norm(coordinates[:, 18] - pelvis, axis=1)
    left_leg = (
        np.linalg.norm(coordinates[:, 11] - coordinates[:, 13], axis=1)
        + np.linalg.norm(coordinates[:, 13] - coordinates[:, 15], axis=1)
    )
    right_leg = (
        np.linalg.norm(coordinates[:, 12] - coordinates[:, 14], axis=1)
        + np.linalg.norm(coordinates[:, 14] - coordinates[:, 16], axis=1)
    )
    stature = head_neck + neck_pelvis + _nanmean(
        np.column_stack((left_leg, right_leg)), axis=1
    )
    bbox_height = bboxes[:, 3] - bboxes[:, 1]
    stature = np.where(np.isfinite(stature) & (stature > 0), stature, bbox_height)
    valid = stature[np.isfinite(stature) & (stature > 0)]
    if valid.size == 0:
        raise ValueError("unable to estimate image stature from pose or bbox")
    return np.where(np.isfinite(stature) & (stature > 0), stature, np.median(valid))


def _height_from_metadata(data: dict) -> float | None:
    containers = [data]
    containers.extend(
        data[name]
        for name in ("runner", "user", "profile", "athlete", "subject")
        if isinstance(data.get(name), dict)
    )
    for container in containers:
        for key in ("height_m", "user_height_m"):
            if key in container:
                value = float(container[key])
                return value if value > 0 else None
        for key in ("height_cm", "user_height_cm"):
            if key in container:
                value = float(container[key]) / 100.0
                return value if value > 0 else None
    return None


def _side_indices(side: str) -> dict[str, int | tuple[int, ...]]:
    if side == "left":
        return {
            "shoulder": 5,
            "elbow": 7,
            "wrist": 9,
            "hip": 11,
            "knee": 13,
            "ankle": 15,
            "toes": (20, 22),
            "heel": 24,
            "foot": (15, 20, 22, 24),
        }
    return {
        "shoulder": 6,
        "elbow": 8,
        "wrist": 10,
        "hip": 12,
        "knee": 14,
        "ankle": 16,
        "toes": (21, 23),
        "heel": 25,
        "foot": (16, 21, 23, 25),
    }


def _interpolate(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    valid = np.isfinite(result)
    if not valid.any():
        raise ValueError("foot coordinates are entirely missing")
    indices = np.arange(len(result))
    result[~valid] = np.interp(indices[~valid], indices[valid], result[valid])
    return result


def _separate_peaks(
    candidates: np.ndarray,
    signal: np.ndarray,
    minimum_distance: int,
) -> np.ndarray:
    selected = []
    for candidate in candidates:
        if not selected or candidate - selected[-1] >= minimum_distance:
            selected.append(int(candidate))
        elif signal[candidate] > signal[selected[-1]]:
            selected[-1] = int(candidate)
    return np.asarray(selected, dtype=int)


def _stance_intervals(
    contacts: np.ndarray,
    signal: np.ndarray,
    baseline: float,
) -> tuple[tuple[int, int], ...]:
    intervals = []
    for contact in contacts:
        threshold = baseline + 0.35 * (signal[contact] - baseline)
        start = int(contact)
        end = int(contact)
        while start > 0 and signal[start - 1] >= threshold:
            start -= 1
        while end + 1 < len(signal) and signal[end + 1] >= threshold:
            end += 1
        intervals.append((start, end))
    return tuple(intervals)


def _running_direction(sequence: PoseSequence) -> int:
    facing = sequence.coordinates[:, 0, 0] - sequence.coordinates[:, 18, 0]
    median_facing = _safe_mean(facing, default=0.0)
    if abs(median_facing) > 1e-6:
        return 1 if median_facing > 0 else -1
    pelvis_x = _nanmean(sequence.coordinates_px[:, [11, 12], 0], axis=1)
    displacement = pelvis_x[-1] - pelvis_x[0]
    return 1 if not np.isfinite(displacement) or displacement >= 0 else -1


def _ordered_contacts(events: GaitEvents) -> list[tuple[int, str]]:
    return sorted(
        (int(frame), side)
        for side in ("left", "right")
        for frame in events.contacts[side]
    )


def _joint_angle(a: np.ndarray, vertex: np.ndarray, c: np.ndarray) -> float:
    first = a - vertex
    second = c - vertex
    denominator = np.linalg.norm(first) * np.linalg.norm(second)
    if not np.isfinite(denominator) or denominator == 0:
        return float("nan")
    cosine = np.clip(np.dot(first, second) / denominator, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def _knee_flexion(points: np.ndarray, idx: dict) -> float:
    return 180.0 - _joint_angle(points[idx["hip"]], points[idx["knee"]], points[idx["ankle"]])


def _elbow_flexion(points: np.ndarray, idx: dict) -> float:
    return 180.0 - _joint_angle(
        points[idx["shoulder"]], points[idx["elbow"]], points[idx["wrist"]]
    )


def _hip_extension(points: np.ndarray, idx: dict) -> float:
    shoulder_center = _nanmean(points[[5, 6]], axis=0)
    return 180.0 - _joint_angle(
        shoulder_center, points[idx["hip"]], points[idx["knee"]]
    )


def _tibia_angle(points: np.ndarray, idx: dict, direction: int) -> float:
    knee = points[idx["knee"]]
    ankle = points[idx["ankle"]]
    angle = np.degrees(
        np.arctan2(ankle[1] - knee[1], direction * (knee[0] - ankle[0]))
    )
    return float(angle % 180.0)


def _foot_angle(points: np.ndarray, idx: dict) -> float:
    heel = points[idx["heel"]]
    toes = _nanmean(points[list(idx["toes"])], axis=0)
    delta = toes - heel
    return float(np.degrees(np.arctan2(abs(delta[1]), abs(delta[0]))))


def _asymmetry(left: float, right: float) -> float:
    if not np.isfinite(left) or not np.isfinite(right):
        return float("nan")
    denominator = (abs(left) + abs(right)) / 2.0
    return 0.0 if denominator == 0 else abs(left - right) / denominator * 100.0


def _nanmean(values: np.ndarray, axis=None) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    count = np.sum(np.isfinite(array), axis=axis)
    total = np.nansum(array, axis=axis)
    with np.errstate(invalid="ignore", divide="ignore"):
        result = total / count
    return np.where(count == 0, np.nan, result)


def _safe_mean(values, default=float("nan")) -> float:
    array = np.asarray(values, dtype=float)
    valid = array[np.isfinite(array)]
    return float(np.mean(valid)) if valid.size else float(default)


def _safe_max(values) -> float:
    array = np.asarray(values, dtype=float)
    valid = array[np.isfinite(array)]
    return float(np.max(valid)) if valid.size else float("nan")


def _safe_range(values) -> float:
    array = np.asarray(values, dtype=float)
    valid = array[np.isfinite(array)]
    return float(np.ptp(valid)) if valid.size else float("nan")


def _safe_std(values) -> float:
    array = np.asarray(values, dtype=float)
    valid = array[np.isfinite(array)]
    return float(np.std(valid)) if valid.size else float("nan")
