"""Run RTMDet + RTMW COCO-WholeBody inference over an image directory."""

import argparse
import json
from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
from typing import Any

from scripts.pose_track import Detection, build_frame_record


IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
RTMW_MODEL_ID = "akore/rtmw-x-384x288"
MODEL_WIDTH = 288
MODEL_HEIGHT = 384


@contextmanager
def trusted_checkpoint_loading(torch: Any):
    """Load the pinned official RTMDet checkpoint on recent PyTorch versions."""
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
    parser.add_argument("--bbox-thr", type=float, default=0.3)
    parser.add_argument("--kpt-thr", type=float, default=0.3)
    return parser.parse_args()


def _as_float_list(values: Any) -> list[float]:
    return [float(value) for value in values]


def _image_paths(input_dir: Path) -> list[Path]:
    return sorted(path for path in input_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)


def prepare_rtmw_inputs(processor: Any, image: Any) -> dict[str, Any]:
    """Prepare the height-384, width-288 tensor expected by RTMW-X."""
    return processor(
        images=image,
        size={"height": MODEL_HEIGHT, "width": MODEL_WIDTH},
        return_tensors="pt",
    )


def repair_rtmw_runtime_buffers(pose_model: Any) -> None:
    gau = pose_model.head.gau
    gau.sqrt_s.fill_(gau.s**0.5)


def serialize_predictions(payload: dict[str, Any]) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
    except ValueError as error:
        raise ValueError(
            "Pose predictions must be JSON-compliant and contain only finite numbers."
        ) from error


def _person_boxes(det_result: Any, bbox_thr: float) -> list[tuple[list[float], float]]:
    instances = det_result.pred_instances.cpu().numpy()
    return [
        (_as_float_list(bbox), float(score))
        for bbox, score, label in zip(
            instances.bboxes, instances.scores, instances.labels, strict=True
        )
        if int(label) == 0 and float(score) >= bbox_thr
    ]


def _predict_person(
    image: Any, bbox: list[float], processor: Any, pose_model: Any, torch: Any, device: str
) -> tuple[list[list[float]], list[float]]:
    left, top, right, bottom = (round(value) for value in bbox)
    person_crop = image.crop((left, top, right, bottom))
    inputs = prepare_rtmw_inputs(processor, person_crop)
    inputs = {name: value.to(device) for name, value in inputs.items()}
    with torch.no_grad():
        outputs = pose_model(**inputs, bbox=bbox, coordinate_mode="image")
    keypoints = outputs.keypoints[0].detach().cpu().tolist()
    scores = outputs.scores[0].detach().cpu().tolist()
    return keypoints, _as_float_list(scores)


def install_mps_nms_fallback(nms_module: Any) -> None:
    """Run MMCV's unsupported MPS NMS operation on CPU only."""
    original_nms = nms_module.nms
    if getattr(original_nms, "_rtmw_mps_fallback", False):
        return

    def nms(boxes: Any, scores: Any, *args: Any, **kwargs: Any) -> tuple[Any, Any]:
        if getattr(getattr(boxes, "device", None), "type", None) != "mps":
            return original_nms(boxes, scores, *args, **kwargs)
        dets, keep = original_nms(boxes.cpu(), scores.cpu(), *args, **kwargs)
        return dets.to(boxes.device), keep

    nms._rtmw_mps_fallback = True
    nms_module.nms = nms


def main() -> None:
    args = parse_args()
    if not args.input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {args.input_dir}")

    import torch
    from PIL import Image
    from mmdet.apis import inference_detector, init_detector
    from mmengine.registry import init_default_scope
    from transformers import AutoImageProcessor, AutoModel

    if args.device == "mps":
        if not torch.backends.mps.is_built() or not torch.backends.mps.is_available():
            raise SystemExit("MPS was requested but is unavailable. Use RTMPOSE_DEVICE=cpu only intentionally.")
        install_mps_nms_fallback(import_module("mmcv.ops.nms"))

    root = Path(__file__).resolve().parents[1]
    detector_config = root / "mmpose/projects/rtmpose/rtmdet/person/rtmdet_nano_320-8xb32_coco-person.py"
    detector_checkpoint = root / "models/rtmdet-nano/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"
    detector = init_detector(str(detector_config), str(detector_checkpoint), device=args.device)
    processor = AutoImageProcessor.from_pretrained(RTMW_MODEL_ID, trust_remote_code=True)
    pose_model = AutoModel.from_pretrained(RTMW_MODEL_ID, trust_remote_code=True)
    repair_rtmw_runtime_buffers(pose_model)
    pose_model = pose_model.to(args.device).eval()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    previous = None
    frames = []
    for image_path in _image_paths(args.input_dir):
        init_default_scope("mmdet")
        with trusted_checkpoint_loading(torch):
            det_result = inference_detector(detector, str(image_path))
        people = _person_boxes(det_result, args.bbox_thr)
        image = Image.open(image_path).convert("RGB")
        detections = []
        for bbox, bbox_score in people:
            keypoints, keypoint_scores = _predict_person(
                image, bbox, processor, pose_model, torch, args.device
            )
            detections.append(Detection(bbox, bbox_score, keypoints, keypoint_scores))
        record, previous = build_frame_record(image_path.name, detections, previous, args.kpt_thr)
        frames.append(record)

    payload = {
        "model": {
            "detector": "RTMDet-nano",
            "pose": "RTMW-X",
            "keypoints": 133,
            "keypoint_format": "COCO-WholeBody",
            "device": args.device,
        },
        "frames": frames,
    }
    output_json = args.output_dir / "pose_predictions.json"
    output_json.write_text(serialize_predictions(payload), encoding="utf-8")
    print(f"Frames processed: {len(frames)}")
    print(f"Predictions: {output_json}")


if __name__ == "__main__":
    main()
