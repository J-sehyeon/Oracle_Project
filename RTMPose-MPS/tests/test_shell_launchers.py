import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = ROOT / "scripts" / "install_rtmpose_mps.sh"
CHECK_SCRIPT = ROOT / "scripts" / "check_rtmpose_environment.sh"


def run_script(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(path), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_install_dry_run_identifies_pinned_openmmlab_sources():
    """Removing an official upstream source from setup must fail this test."""
    result = run_script(INSTALL_SCRIPT, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "open-mmlab/mmpose" in result.stdout
    assert "open-mmlab/mmdetection" in result.stdout
    assert "setuptools<81" in result.stdout
    assert "MMCV build isolation: disabled" in result.stdout
    assert "Editable package build isolation: disabled" in result.stdout
    assert "jin-s13/xtcocoapi" in result.stdout
    assert "v1.14.3" in result.stdout
    assert "MMDetection .mim config links: enabled" in result.stdout
    assert "MMPose .mim config links: enabled" in result.stdout


def test_checker_dry_run_lists_mps_and_rtmw_dependencies():
    """The environment check must name the RTMW model and its runtime."""
    result = run_script(CHECK_SCRIPT, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "MPS" in result.stdout
    assert "RTMDet-nano" in result.stdout
    assert "RTMW-X" in result.stdout
    assert "Transformers" in result.stdout
