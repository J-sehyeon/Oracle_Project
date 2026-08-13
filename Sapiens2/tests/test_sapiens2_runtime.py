import pytest
import torch
from safetensors.torch import save_file

from scripts.sapiens2_runtime import (
    select_device,
    validate_checkpoint_dtype,
    validate_safetensors_file,
)


def test_auto_device_prefers_mps_when_available():
    assert select_device("auto", mps_available=True) == torch.device("mps")


def test_auto_device_falls_back_to_cpu_without_mps():
    assert select_device("auto", mps_available=False) == torch.device("cpu")


def test_explicit_mps_fails_when_unavailable():
    with pytest.raises(RuntimeError, match="MPS was requested"):
        select_device("mps", mps_available=False)


@pytest.mark.parametrize("dtype", [torch.float32, torch.float16, torch.bfloat16])
def test_float_checkpoint_dtypes_are_accepted(dtype):
    validate_checkpoint_dtype({"weight": torch.zeros(2, dtype=dtype)})


@pytest.mark.parametrize("dtype", [torch.int8, torch.uint8, torch.int32])
def test_quantized_integer_checkpoint_dtypes_are_rejected(dtype):
    with pytest.raises(ValueError, match="quantized or integer"):
        validate_checkpoint_dtype({"weight": torch.zeros(2, dtype=dtype)})


def test_floating_point_safetensors_file_is_accepted(tmp_path):
    checkpoint = tmp_path / "model.safetensors"
    save_file({"weight": torch.zeros(2, dtype=torch.float32)}, checkpoint)

    assert validate_safetensors_file(checkpoint) == {"F32": 1}


def test_integer_safetensors_file_is_rejected(tmp_path):
    checkpoint = tmp_path / "model.safetensors"
    save_file({"weight": torch.zeros(2, dtype=torch.int8)}, checkpoint)

    with pytest.raises(ValueError, match="quantized or integer"):
        validate_safetensors_file(checkpoint)


def test_batchnorm_tracking_counter_is_not_misclassified_as_quantization(tmp_path):
    checkpoint = tmp_path / "model.safetensors"
    save_file(
        {
            "backbone.bn.weight": torch.ones(2, dtype=torch.float32),
            "backbone.bn.num_batches_tracked": torch.zeros((), dtype=torch.int64),
        },
        checkpoint,
    )

    assert validate_safetensors_file(checkpoint) == {"I64": 1, "F32": 1}
