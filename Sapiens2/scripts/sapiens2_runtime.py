"""Runtime and precision guards for Sapiens2 on Apple Silicon."""

from collections.abc import Mapping
from pathlib import Path

import torch
from safetensors import safe_open


def select_device(
    preferred: str = "auto", *, mps_available: bool | None = None
) -> torch.device:
    """Select MPS by default and use CPU only when Metal is unavailable."""
    if preferred not in {"auto", "mps", "cpu"}:
        raise ValueError(f"Unsupported device: {preferred}")

    if mps_available is None:
        mps_available = torch.backends.mps.is_available()

    if preferred == "mps" and not mps_available:
        raise RuntimeError("MPS was requested but is not available")
    if preferred == "cpu":
        return torch.device("cpu")
    if mps_available:
        return torch.device("mps")
    return torch.device("cpu")


def validate_checkpoint_dtype(state_dict: Mapping[str, torch.Tensor]) -> None:
    """Reject integer checkpoint tensors to prevent accidental quantized use."""
    invalid = sorted(
        name
        for name, tensor in state_dict.items()
        if isinstance(tensor, torch.Tensor)
        and not (tensor.is_floating_point() or tensor.is_complex())
    )
    if invalid:
        names = ", ".join(invalid[:5])
        raise ValueError(
            "Checkpoint contains quantized or integer tensors: "
            f"{names}. Use Meta's original floating-point safetensors checkpoint."
        )


def validate_safetensors_file(path: str | Path) -> dict[str, int]:
    """Inspect metadata and reject low-bit parameters without loading weights."""
    dtype_counts: dict[str, int] = {}
    invalid: list[str] = []
    with safe_open(str(path), framework="pt", device="cpu") as checkpoint:
        for name in checkpoint.keys():
            dtype = checkpoint.get_slice(name).get_dtype()
            dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
            is_batchnorm_counter = (
                name.endswith(".num_batches_tracked") and dtype == "I64"
            )
            if dtype not in {"F32", "F16", "BF16"} and not is_batchnorm_counter:
                invalid.append(f"{name}:{dtype}")

    if invalid:
        names = ", ".join(invalid[:5])
        raise ValueError(
            "Checkpoint contains quantized or integer tensors: "
            f"{names}. Parameters must be F32, F16, or BF16; only I64 "
            "BatchNorm tracking counters are exempt."
        )
    return dtype_counts
