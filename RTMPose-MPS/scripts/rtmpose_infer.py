"""Run official RTMDet + RTMPose inference over an image directory."""

import argparse
import json
from importlib import import_module
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from scripts.pose_track import Detection, build_frame_record
from scripts.rtmpose_config import select_model_paths


IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}


@contextmanager
def trusted_checkpoint_loading(torch: Any):
    """Load the pinned official checkpoint on PyTorch versions with safe defaults."""
    original_load = torch.load

    def load(*args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("weights_only", False)
        return original_load(*args, **kwargs)

    torch.load = load
    try:
        yield
    finally:
        torch.load = original_load


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--device", choices=("mps", "cpu"), required=True)
    parser.add_argument("--variant", choices=("m", "s", "halpe26"), default="m")
    parser.add_argument("--bbox-thr", type=float, default=0.3)
    parser.add_argument("--kpt-thr", type=float, default=0.3)
    return parser.parse_args()


def _as_float_list(values: Any) -> list[float]:
    return [float(value) for value in values]


def model_metadata(variant: str, device: str) -> dict[str, Any]:
    if variant == "halpe26":
        return {
            "detector": "RTMDet-nano",
            "pose": "RTMPose-M Halpe-26",
            "keypoints": 26,
            "keypoint_format": "Halpe-26",
            "device": device,
        }
    return {
        "detector": "RTMDet-nano",
        "pose": f"RTMPose-{variant.upper()}",
        "keypoints": 17,
        "device": device,
    }


def _detections_from_results(
    det_result: Any, pose_results: list[Any], bbox_thr: float
) -> list[Detection]:
    instances = det_result.pred_instances.cpu().numpy()
    people = [
        (bbox, float(score))
        for bbox, score, label in zip(
            instances.bboxes, instances.scores, instances.labels, strict=True
        )
        if int(label) == 0 and float(score) >= bbox_thr
    ]
    detections: list[Detection] = []
    for (bbox, bbox_score), pose_result in zip(people, pose_results, strict=True):
        prediction = pose_result.pred_instances
        detections.append(
            Detection(
                bbox=_as_float_list(bbox),
                bbox_score=bbox_score,
                keypoints=[_as_float_list(point) for point in prediction.keypoints[0]],
                keypoint_scores=_as_float_list(prediction.keypoint_scores[0]),
            )
        )
    return detections


def _image_paths(input_dir: Path) -> list[Path]:
    return sorted(path for path in input_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)


def run_topdown_inference(
    detector: Any,
    pose_model: Any,
    image_path: str,
    bbox_thr: float,
    init_default_scope: Any,
    inference_detector: Any,
    inference_topdown: Any,
) -> tuple[Any, list[Any]]:
    init_default_scope("mmdet")
    det_result = inference_detector(detector, image_path)
    instances = det_result.pred_instances.cpu().numpy()
    person_boxes = [
        bbox
        for bbox, score, label in zip(
            instances.bboxes, instances.scores, instances.labels, strict=True
        )
        if int(label) == 0 and float(score) >= bbox_thr
    ]
    init_default_scope("mmpose")
    return det_result, inference_topdown(pose_model, image_path, person_boxes)


def install_mps_nms_fallback(nms_module: Any) -> None:
    """Run MMCV's unsupported MPS NMS operation on CPU only."""
    original_nms = nms_module.nms
    if getattr(original_nms, "_rtmpose_mps_fallback", False):
        return

    def nms(boxes: Any, scores: Any, *args: Any, **kwargs: Any) -> tuple[Any, Any]:
        if getattr(getattr(boxes, "device", None), "type", None) != "mps":
            return original_nms(boxes, scores, *args, **kwargs)
        dets, keep = original_nms(boxes.cpu(), scores.cpu(), *args, **kwargs)
        return dets.to(boxes.device), keep

    nms._rtmpose_mps_fallback = True
    nms_module.nms = nms


def main() -> None:
    args = parse_args()
    if not args.input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {args.input_dir}")
    import torch

    if args.device == "mps":
        if not torch.backends.mps.is_built() or not torch.backends.mps.is_available():
            raise SystemExit("MPS was requested but is unavailable. Use RTMPOSE_DEVICE=cpu only intentionally.")

    from mmdet.apis import inference_detector, init_detector
    from mmengine.registry import init_default_scope
    from mmpose.apis import inference_topdown, init_model

    if args.device == "mps":
        install_mps_nms_fallback(import_module("mmcv.ops.nms"))

    root = Path(__file__).resolve().parents[1]
    paths = select_model_paths(root, args.variant)
    detector = init_detector(
        str(paths.detector_config), str(paths.detector_checkpoint), device=args.device
    )
    with trusted_checkpoint_loading(torch):
        pose_model = init_model(
            str(paths.pose_config), str(paths.pose_checkpoint), device=args.device
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    previous = None
    frames = []
    for image_path in _image_paths(args.input_dir):
        det_result, pose_results = run_topdown_inference(
            detector,
            pose_model,
            str(image_path),
            args.bbox_thr,
            init_default_scope,
            inference_detector,
            inference_topdown,
        )
        detections = _detections_from_results(det_result, pose_results, args.bbox_thr)
        record, previous = build_frame_record(
            image_path.name, detections, previous, args.kpt_thr
        )
        frames.append(record)
    payload = {
        "model": model_metadata(args.variant, args.device),
        "frames": frames,
    }
    output_json = args.output_dir / "pose_predictions.json"
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Frames processed: {len(frames)}")
    print(f"Predictions: {output_json}")


if __name__ == "__main__":
    main()
