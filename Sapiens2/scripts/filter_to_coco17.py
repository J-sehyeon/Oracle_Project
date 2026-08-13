import argparse
import json
from pathlib import Path

import cv2

# Sapiens2-308에서 그대로 가져올 관절. 손목 인덱스는 연속적이지 않다.
FIXED_KEYPOINTS = [
    ("right_eye", 2),
    ("right_ear", 4),
    ("left_shoulder", 5),
    ("right_shoulder", 6),
    ("left_elbow", 7),
    ("right_elbow", 8),
    ("left_wrist", 62),
    ("right_wrist", 41),
    ("left_hip", 9),
    ("right_hip", 10),
    ("left_knee", 11),
    ("right_knee", 12),
    ("left_ankle", 13),
    ("right_ankle", 14),
]

# 발가락은 엄지/새끼 중 confidence가 높은 한 점만 남긴다.
TOE_CANDIDATES = {
    "left_toe": (15, 16),
    "right_toe": (18, 19),
}

HEEL_KEYPOINTS = [
    ("left_heel", 17),
    ("right_heel", 20),
]

# 필터링된 body18 인덱스끼리의 연결
LINKS = [
    (0, 1), (1, 3),  # right eye -> ear -> shoulder
    (2, 3),
    (2, 4), (4, 6),
    (3, 5), (5, 7),
    (2, 8), (3, 9), (8, 9),
    (8, 10), (10, 12), (9, 11), (11, 13),
    (12, 14), (12, 16),
    (13, 15), (13, 17),
]

NAMES = [
    name for name, _ in FIXED_KEYPOINTS
] + [
    "left_toe", "right_toe",
] + [
    name for name, _ in HEEL_KEYPOINTS
]


def select_keypoints(person):
    """Return the selected body18 points, scores, and Sapiens2 source ids."""
    raw_points = person["keypoints"]
    raw_scores = person["keypoint_scores"]

    source_ids = [source_id for _, source_id in FIXED_KEYPOINTS]
    for candidate_ids in TOE_CANDIDATES.values():
        source_ids.append(max(candidate_ids, key=lambda source_id: raw_scores[source_id]))
    source_ids.extend(source_id for _, source_id in HEEL_KEYPOINTS)

    return (
        [raw_points[source_id] for source_id in source_ids],
        [raw_scores[source_id] for source_id in source_ids],
        source_ids,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--frames-dir", required=True,
                        help="포즈가 그려지지 않은 원본 PNG/JPG 프레임 폴더")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--threshold", type=float, default=0.3)
    args = parser.parse_args()

    source = json.loads(Path(args.input_json).read_text())
    frame_dir = Path(args.frames_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filtered_frames = []

    for frame in source["frames"]:
        image = cv2.imread(str(frame_dir / frame["image_name"]))
        if image is None:
            print(f"Skipping missing image: {frame['image_name']}")
            continue

        instances = []
        for person in frame["instances"]:
            points, scores, source_ids = select_keypoints(person)

            # 뼈대
            for a, b in LINKS:
                if scores[a] >= args.threshold and scores[b] >= args.threshold:
                    pa = tuple(round(v) for v in points[a])
                    pb = tuple(round(v) for v in points[b])
                    cv2.line(image, pa, pb, (0, 220, 0), 2)

            # 관절
            for point, score in zip(points, scores):
                if score >= args.threshold:
                    cv2.circle(
                        image, tuple(round(v) for v in point),
                        4, (0, 80, 255), -1
                    )

            instances.append({
                "bbox": person["bbox"],
                "keypoints": points,
                "keypoint_scores": scores,
                "source_keypoint_ids": source_ids,
            })

        cv2.imwrite(str(output_dir / frame["image_name"]), image)
        filtered_frames.append({
            "image_name": frame["image_name"],
            "instances": instances,
        })

    result = {
        "video": source.get("video"),
        "image_size": source.get("image_size"),
        "format": "sapiens2_body18_v1",
        "keypoint_names": NAMES,
        "num_keypoints": len(NAMES),
        "toe_selection": "highest-confidence of big toe or small toe per foot",
        "kpt_thr_used": args.threshold,
        "frames": filtered_frames,
    }
    out_json = output_dir / "coco17_predictions.json"
    out_json.write_text(json.dumps(result, ensure_ascii=False))
    print(f"Wrote: {out_json}")


if __name__ == "__main__":
    main()
