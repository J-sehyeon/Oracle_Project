import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_SCRIPT = ROOT / "scripts" / "run_rtmpose_pose.sh"


def run_script(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(RUN_SCRIPT), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_dry_run_defaults_to_mps_rtmw_x_and_coco_wholebody(tmp_path: Path):
    """The production launcher must advertise the RTMW WholeBody contract."""
    images = tmp_path / "images"
    images.mkdir()

    result = run_script("--dry-run", str(images))

    assert result.returncode == 0, result.stderr
    assert "--device mps" in result.stdout
    assert "scripts.rtmw_infer" in result.stdout
    assert "RTMW-X" in result.stdout
    assert "133 whole-body keypoints" in result.stdout


def test_dry_run_allows_only_explicit_cpu_override(tmp_path: Path):
    """Making CPU the implicit fallback would hide failed MPS execution."""
    images = tmp_path / "images"
    images.mkdir()

    result = subprocess.run(
        ["/bin/bash", str(RUN_SCRIPT), "--dry-run", str(images)],
        cwd=ROOT,
        env={"RTMPOSE_DEVICE": "cpu"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--device cpu" in result.stdout


def test_dry_run_selects_halpe26_hpe_while_preserving_mps_detection(tmp_path: Path):
    """Changing the HPE model must not replace the RTMDet/MPS runtime contract."""
    images = tmp_path / "images"
    images.mkdir()

    result = run_script(
        "--dry-run",
        str(images),
        env={"RTMPOSE_HPE_MODEL": "halpe26"},
    )

    assert result.returncode == 0, result.stderr
    assert "--device mps" in result.stdout
    assert "scripts.rtmpose_infer" in result.stdout
    assert "--variant halpe26" in result.stdout
    assert "RTMPose-M Halpe-26" in result.stdout
    assert "26 keypoints" in result.stdout
