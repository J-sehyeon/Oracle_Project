"""Extract running features from a Body18 pose-coordinate JSON file."""

import argparse
import json
import math
import statistics
from pathlib import Path


DISTANCE_UNIT = "% body_reference"


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _centre(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def _median(values):
    return statistics.median(values) if values else None


def angle_degrees(a, b, c):
    """Return the unsigned 0..180 degree angle ABC."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    length = math.hypot(*ba) * math.hypot(*bc)
    if not length:
        return None
    cosine = max(-1.0, min(1.0, (ba[0] * bc[0] + ba[1] * bc[1]) / length))
    return math.degrees(math.acos(cosine))


def load_pose_frames(payload, threshold=0.3):
    """Convert Body18 JSON into frames containing confident named keypoints."""
    names = payload.get("keypoint_names", [])
    result = []
    for frame_index, frame in enumerate(payload.get("frames", [])):
        instances = frame.get("instances", [])
        if not instances:
            continue
        instance = instances[0]
        points = {}
        for name, point, score in zip(
            names, instance.get("keypoints", []), instance.get("keypoint_scores", [])
        ):
            if score >= threshold and len(point) >= 2:
                points[name] = (float(point[0]), float(point[1]))
        result.append({"frame": frame_index, "points": points})
    return result


def _p(frame, *names):
    points = frame["points"]
    values = [points[name] for name in names if name in points]
    return values if len(values) == len(names) else None


def _hip_centre(frame):
    points = _p(frame, "left_hip", "right_hip")
    return _centre(*points) if points else None


def _shoulder_centre(frame):
    points = _p(frame, "left_shoulder", "right_shoulder")
    return _centre(*points) if points else None


def body_reference(frames):
    """Return median torso + average leg length, measured in pixels."""
    lengths = []
    for frame in frames:
        shoulder = _shoulder_centre(frame)
        hip = _hip_centre(frame)
        left = _p(frame, "left_hip", "left_knee", "left_ankle")
        right = _p(frame, "right_hip", "right_knee", "right_ankle")
        if not (shoulder and hip and left and right):
            continue
        torso = _distance(shoulder, hip)
        left_leg = _distance(left[0], left[1]) + _distance(left[1], left[2])
        right_leg = _distance(right[0], right[1]) + _distance(right[1], right[2])
        lengths.append(torso + (left_leg + right_leg) / 2)
    return _median(lengths)


def _smooth(values):
    return [
        sum(values[max(0, i - 1):min(len(values), i + 2)]) /
        len(values[max(0, i - 1):min(len(values), i + 2)])
        for i in range(len(values))
    ]


def _extrema(samples, minimum_gap):
    """Return local maxima (IC) and minima (TO) from y-down image samples."""
    if len(samples) < 3:
        return [], []
    indices, values = zip(*samples)
    smooth = _smooth(values)
    initial_contacts, toe_offs = [], []
    for i in range(1, len(smooth) - 1):
        maximum = smooth[i] >= smooth[i - 1] and smooth[i] > smooth[i + 1]
        minimum = smooth[i] <= smooth[i - 1] and smooth[i] < smooth[i + 1]
        if maximum and (not initial_contacts or indices[i] - initial_contacts[-1] >= minimum_gap):
            initial_contacts.append(indices[i])
        if minimum and (not toe_offs or indices[i] - toe_offs[-1] >= minimum_gap):
            toe_offs.append(indices[i])
    return initial_contacts, toe_offs


def detect_gait_events(frames, fps):
    """Detect per-foot IC/TO from smoothed vertical foot trajectories."""
    events = {}
    for side in ("left", "right"):
        samples = []
        for frame in frames:
            foot_points = _p(frame, f"{side}_ankle", f"{side}_toe", f"{side}_heel")
            if foot_points:
                samples.append((frame["frame"], sum(point[1] for point in foot_points) / 3))
        ic, to = _extrema(samples, minimum_gap=max(2, round(fps * 0.12)))
        events[side] = {"initial_contact": ic, "toe_off": to}
    return events


def _pairs_after(starts, ends):
    return [(start, next((end for end in ends if end > start), None)) for start in starts]


def _feature(value, unit, reason=None, height_cm=None):
    result = {"value": value, "unit": unit}
    if reason:
        result["reason"] = reason
    if value is not None and height_cm is not None and unit == DISTANCE_UNIT:
        result["estimated_cm"] = value * height_cm / 100
    return result


def _frame_lookup(frames):
    return {frame["frame"]: frame for frame in frames}


def _phase_values(frames, events, callback):
    lookup = _frame_lookup(frames)
    values = []
    for side, side_events in events.items():
        for number in side_events["initial_contact"]:
            value = callback(lookup[number], side)
            if value is not None:
                values.append(value)
    return values


def analyze_pose_json(payload, fps=25, height_cm=None, threshold=0.3):
    """Return auditable feature values from a Body18 pose JSON payload."""
    if fps <= 0:
        raise ValueError("fps must be greater than zero")
    if height_cm is not None and height_cm <= 0:
        raise ValueError("height_cm must be greater than zero")

    frames = load_pose_frames(payload, threshold)
    reference = body_reference(frames)
    events = detect_gait_events(frames, fps)
    unavailable = "Insufficient confident pose coordinates or gait events."

    trunk = []
    pelvis = []
    hip_y = []
    for frame in frames:
        shoulder, hip = _shoulder_centre(frame), _hip_centre(frame)
        if shoulder and hip:
            trunk.append(math.degrees(math.atan2(shoulder[0] - hip[0], hip[1] - shoulder[1])))
            hip_y.append(hip[1])
        pair = _p(frame, "left_hip", "right_hip")
        if pair:
            pelvis.append(abs(math.degrees(math.atan2(pair[1][1] - pair[0][1], pair[1][0] - pair[0][0]))))

    def knee_flexion(frame, side):
        points = _p(frame, f"{side}_hip", f"{side}_knee", f"{side}_ankle")
        angle = angle_degrees(*points) if points else None
        return 180 - angle if angle is not None else None

    direction = 1
    hips = [_hip_centre(frame) for frame in frames]
    hips = [hip for hip in hips if hip]
    if len(hips) > 1 and hips[-1][0] < hips[0][0]:
        direction = -1

    def foot_angle(frame, side):
        points = _p(frame, f"{side}_heel", f"{side}_toe")
        if not points:
            return None
        heel, toe = points
        return math.degrees(math.atan2(heel[1] - toe[1], abs(toe[0] - heel[0])))

    def overstride(frame, side):
        ankle = _p(frame, f"{side}_ankle")
        hip = _hip_centre(frame)
        if not (ankle and hip and reference):
            return None
        return direction * (ankle[0][0] - hip[0]) / reference * 100

    knee_values = _phase_values(frames, events, knee_flexion)
    foot_values = _phase_values(frames, events, foot_angle)
    overstride_values = _phase_values(frames, events, overstride)

    contact_times = {}
    flight_times = []
    stride_times = []
    for side, side_events in events.items():
        ics, tos = side_events["initial_contact"], side_events["toe_off"]
        contacts = [(to - ic) / fps * 1000 for ic, to in _pairs_after(ics, tos) if to is not None]
        contact_times[side] = contacts
        for to in tos:
            next_ic = next((ic for ic in ics if ic > to), None)
            if next_ic is not None:
                flight_times.append((next_ic - to) / fps * 1000)
        stride_times.extend((later - earlier) / fps for earlier, later in zip(ics, ics[1:]))

    all_contacts = sorted(
        contact for side_events in events.values()
        for contact in side_events["initial_contact"]
    )
    cadence_intervals = [later - earlier for earlier, later in zip(all_contacts, all_contacts[1:])]
    cadence = 60 * fps / _median(cadence_intervals) if cadence_intervals else None
    left_gct, right_gct = _median(contact_times["left"]), _median(contact_times["right"])
    asymmetry = None
    if left_gct is not None and right_gct is not None and left_gct + right_gct:
        asymmetry = abs(left_gct - right_gct) / ((left_gct + right_gct) / 2) * 100
    stride_cv = None
    if len(stride_times) >= 2 and statistics.mean(stride_times):
        stride_cv = statistics.stdev(stride_times) / statistics.mean(stride_times) * 100

    vertical = (max(hip_y) - min(hip_y)) / reference * 100 if hip_y and reference else None
    result = {
        "input_format": payload.get("format"), "fps": fps,
        "body_reference_px": reference, "distance_normalization": DISTANCE_UNIT,
        "events": events,
        "features": {
            "FEAT-01": _feature(_median(trunk), "degrees", unavailable if not trunk else None),
            "FEAT-02": _feature(_median(knee_values), "degrees", unavailable if not knee_values else None),
            "FEAT-03": _feature(cadence, "steps/min", unavailable if cadence is None else None),
            "FEAT-04": _feature(_median(contact_times["left"] + contact_times["right"]), "ms", unavailable if not (contact_times["left"] + contact_times["right"]) else None),
            "FEAT-05": _feature(_median(flight_times), "ms", unavailable if not flight_times else None),
            "FEAT-06": _feature(vertical, DISTANCE_UNIT, unavailable if vertical is None else None, height_cm),
            "FEAT-07": _feature(_median(foot_values), "degrees", unavailable if not foot_values else None),
            "FEAT-08": _feature(_median(overstride_values), DISTANCE_UNIT, unavailable if not overstride_values else None, height_cm),
            "FEAT-09": _feature(_median(pelvis), "degrees", unavailable if not pelvis else None),
            "FEAT-10": _feature(asymmetry, "percent", unavailable if asymmetry is None else None),
            "FEAT-11": _feature(stride_cv, "percent", "At least two stride intervals are required." if stride_cv is None else None),
            "FEAT-12": _feature(None, "BW/s", "Force-plate GRF data is required; pose coordinates alone cannot directly measure vertical loading rate."),
        },
    }
    if height_cm is not None:
        result["height_cm_for_estimates"] = height_cm
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--fps", type=float, default=25)
    parser.add_argument("--height-cm", type=float)
    parser.add_argument("--threshold", type=float, default=0.3)
    args = parser.parse_args()
    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = analyze_pose_json(payload, args.fps, args.height_cm, args.threshold)
    Path(args.output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
