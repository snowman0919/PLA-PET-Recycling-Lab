#!/usr/bin/env python3
"""Validate stored RTX stability evidence without requiring a GPU in CI."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    path = ROOT / "simulation" / "gpu" / "two_tower_stability_gpu.json"
    result = json.loads(path.read_text())
    assert result["backend"] == "CUDA"
    assert result["device_name"] == "NVIDIA GeForce RTX 3080"
    assert result["sample_count"] >= 1 << 22
    assert result["kernel_elapsed_ms"] > 0
    assert result["cpu_gpu_crosscheck_samples"] >= 8192
    assert result["cpu_gpu_max_abs_error_n"] <= result["acceptance"]["cpu_gpu_max_abs_error_n"]
    assert result["unanchored_overturn_probability"] >= result["acceptance"]["unanchored_overturn_probability_min"]
    assert result["anchor_pair_tension_p99_n"] <= result["acceptance"]["anchor_pair_tension_p99_max_n"]
    assert result["anchor_pair_capacity_exceed_probability"] <= result["acceptance"]["anchor_pair_capacity_exceed_probability_max"]

    contract = ROOT / "simulation" / "architecture" / "two_tower_contract.json"
    source = ROOT / "simulation" / "gpu" / "two_tower_stability.cu"
    assert result["contract_sha256"] == hashlib.sha256(contract.read_bytes()).hexdigest()
    assert result["cuda_source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert result["status"] == "VIRTUAL_SIMULATION_EVIDENCE_NOT_PHYSICAL_VALIDATION"
    print("TWO_TOWER_GPU_EVIDENCE_VALIDATION_OK")


if __name__ == "__main__":
    main()
