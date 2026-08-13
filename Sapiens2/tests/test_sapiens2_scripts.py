import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_SCRIPT = ROOT / "scripts" / "download_sapiens2_models.sh"
RUN_SCRIPT = ROOT / "scripts" / "run_sapiens2_pose.sh"
CHECK_SCRIPT = ROOT / "scripts" / "check_sapiens2_environment.sh"


def run_script(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(path), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_download_dry_run_uses_official_unquantized_checkpoint():
    result = run_script(DOWNLOAD_SCRIPT, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "facebook/sapiens2-pose-0.4b" in result.stdout
    assert "sapiens2_0.4b_pose.safetensors" in result.stdout
    assert "facebook/detr-resnet-101-dc5" in result.stdout
    assert "Quantization: disabled" in result.stdout


def test_scripts_do_not_enable_low_bit_quantization():
    forbidden = ("load_in_4bit", "load_in_8bit", "bitsandbytes", "--quantize")
    contents = DOWNLOAD_SCRIPT.read_text() + RUN_SCRIPT.read_text()

    assert not any(token in contents for token in forbidden)


def test_pose_launcher_dry_run_selects_smallest_pose_model(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    result = run_script(
        RUN_SCRIPT,
        "--dry-run",
        str(input_dir),
        str(output_dir),
    )

    assert result.returncode == 0, result.stderr
    assert "sapiens2_0.4b_pose.safetensors" in result.stdout
    assert "--device" in result.stdout
    assert "PYTORCH_ENABLE_MPS_FALLBACK=1" in result.stdout


def test_pose_launcher_resolves_relative_io_paths_before_changing_directory():
    temp_root = ROOT / "tmp"
    temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_root) as input_dir:
        relative_input = Path(input_dir).relative_to(ROOT)
        relative_output = Path("outputs/sapiens2/relative-path-test")

        result = run_script(
            RUN_SCRIPT,
            "--dry-run",
            str(relative_input),
            str(relative_output),
        )

    assert result.returncode == 0, result.stderr
    assert str((ROOT / relative_input).resolve()) in result.stdout
    assert str((ROOT / relative_output).resolve()) in result.stdout


def test_environment_checker_dry_run_lists_critical_checks():
    result = run_script(CHECK_SCRIPT, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "Python 3.12" in result.stdout
    assert "PyTorch" in result.stdout
    assert "MPS" in result.stdout
    assert "Sapiens2" in result.stdout
    assert "Checkpoint dtype" in result.stdout
