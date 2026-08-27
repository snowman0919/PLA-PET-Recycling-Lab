#!/usr/bin/env python3
"""Run the compiled CUDA stability sweep and attach traceability metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def output(command: list[str]) -> str:
    return subprocess.run(command, check=True, text=True, capture_output=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--samples", type=int, default=1 << 22)
    args = parser.parse_args()

    raw = output([str(args.executable.resolve()), str(args.samples)])
    result = json.loads(raw)
    contract = ROOT / "simulation" / "architecture" / "two_tower_contract.json"
    source = ROOT / "simulation" / "gpu" / "two_tower_stability.cu"
    result.update(
        {
            "status": "VIRTUAL_SIMULATION_EVIDENCE_NOT_PHYSICAL_VALIDATION",
            "geometry_revision": "two_tower_contract_v1",
            "git_head": output(["git", "rev-parse", "HEAD"]),
            "contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
            "cuda_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "command": f"two_tower_stability {args.samples}",
            "compiler": "Nix cuda_nvcc 12.9.86",
            "build_mode": "nvcc -O3 -std=c++17; CUDA kernel plus 8192-sample host cross-check",
            "uncertainty_model": {
                "tower_a_mass": "uniform 80 to 120 percent of 57.5 kg",
                "vertical_cg_m": "uniform 0.6254 to 0.7254",
                "operating_acceleration_g": "uniform 0.25 to 0.45",
                "cutter_force_n": "uniform 40 to 100",
                "cutter_force_height_m": "uniform 0.8925 to 0.9925",
                "dynamic_factor": "uniform 1.20 to 1.80",
                "base_depth_m": "uniform 0.58 to 0.62",
                "anchor_pair_capacity_n": 2000.0,
            },
            "acceptance": {
                "cpu_gpu_max_abs_error_n": 1e-9,
                "anchor_pair_tension_p99_max_n": 1000.0,
                "anchor_pair_capacity_exceed_probability_max": 1e-6,
                "unanchored_overturn_probability_min": 0.05,
            },
            "interpretation": "Anchors are required because plausible operating uncertainty produces unanchored overturning; the 2 kN pair candidate remains a screening value pending substrate pullout tests.",
        }
    )
    path = ROOT / "simulation" / "gpu" / "two_tower_stability_gpu.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print("TWO_TOWER_GPU_STABILITY_OK")


if __name__ == "__main__":
    main()
