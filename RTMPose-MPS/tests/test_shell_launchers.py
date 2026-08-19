import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = ROOT / "scripts" / "install_rtmpose_mps.sh"
CHECK_SCRIPT = ROOT / "scripts" / "check_rtmpose_environment.sh"
DOWNLOAD_SCRIPT = ROOT / "scripts" / "download_rtmw_models.sh"


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
    assert "HPE model: rtmw" in result.stdout


def test_checker_dry_run_identifies_the_selected_halpe26_model():
    """Reporting the default model for Halpe runs would hide missing-model diagnostics."""
    result = subprocess.run(
        ["/bin/bash", str(CHECK_SCRIPT), "--dry-run"],
        cwd=ROOT,
        env={"RTMPOSE_HPE_MODEL": "halpe26"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "HPE model: halpe26" in result.stdout
    assert "RTMPose-M Halpe-26 checkpoint" in result.stdout


def test_model_download_dry_run_includes_the_halpe26_checkpoint():
    """Omitting Halpe-26 from model setup would leave its launcher branch unusable."""
    result = run_script(DOWNLOAD_SCRIPT, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "RTMDet-nano" in result.stdout
    assert "RTMW-X" in result.stdout
    assert "RTMPose-M Halpe-26" in result.stdout
    assert "89e6428b" in result.stdout
