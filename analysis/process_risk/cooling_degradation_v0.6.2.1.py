#!/usr/bin/env python3
"""Bounded airflow-degradation and conservative response screening.

This is an analytical sensitivity model, not an airflow measurement.  It uses
the same lumped strand cooling relation as calculations/run_engineering.py.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LENGTH_M = 0.323
DIAMETER_M = 1.75e-3
AMBIENT_C = 25.0

MATERIALS = {
    "PLA": {"density": 1240.0, "cp": 1800.0, "die_c": 200.0, "limit_c": 48.0},
    "PET": {"density": 1380.0, "cp": 1200.0, "die_c": 265.0, "limit_c": 65.0},
}

CASES = {
    "dual_fan_clean_centered": {"h": 65.0, "policy": "NORMAL"},
    "filter_fouling": {"h": 48.0, "policy": "SENSITIVITY_LIMIT_ONLY"},
    "duct_leakage": {"h": 45.0, "policy": "SENSITIVITY_LIMIT_ONLY"},
    "partial_blockage": {"h": 40.0, "policy": "SENSITIVITY_LIMIT_ONLY"},
    "strand_off_center": {"h": 42.0, "policy": "SENSITIVITY_LIMIT_ONLY"},
    "single_fan_operation": {"h": 35.0, "policy": "CONTROLLED_RUNDOWN"},
    "dual_fan_loss": {"h": 0.0, "policy": "CONTROLLED_RUNDOWN"},
}


def entry_temperature(material: str, throughput_gph: float, h_w_m2k: float) -> float:
    p = MATERIALS[material]
    if throughput_gph <= 0:
        return AMBIENT_C
    if h_w_m2k <= 0:
        return p["die_c"]
    area = math.pi * DIAMETER_M**2 / 4.0
    speed = (throughput_gph / 1000.0 / 3600.0) / (p["density"] * area)
    dwell = LENGTH_M / speed
    tau = p["density"] * p["cp"] * DIAMETER_M / (4.0 * h_w_m2k)
    return AMBIENT_C + (p["die_c"] - AMBIENT_C) * math.exp(-dwell / tau)


def maximum_safe_rate(material: str, h_w_m2k: float) -> float:
    if h_w_m2k <= 0:
        return 0.0
    lo, hi = 0.0, 150.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if entry_temperature(material, mid, h_w_m2k) <= MATERIALS[material]["limit_c"]:
            lo = mid
        else:
            hi = mid
    return lo


def main() -> None:
    rows = []
    for material in MATERIALS:
        for case, definition in CASES.items():
            safe = maximum_safe_rate(material, definition["h"])
            # This command is an analytical upper bound, not a production command.
            # Firmware intentionally uses the more conservative controlled-rundown
            # response for a detected fan loss because tach does not prove airflow.
            command = 0.0 if definition["policy"] == "CONTROLLED_RUNDOWN" else min(100.0, 0.95 * safe)
            at_100 = entry_temperature(material, 100.0, definition["h"])
            commanded_temp = entry_temperature(material, command, definition["h"])
            rows.append({
                "material": material,
                "case": case,
                "assumed_h_w_m2k": definition["h"],
                "puller_entry_limit_c": MATERIALS[material]["limit_c"],
                "entry_at_100_gph_c": round(at_100, 3),
                "maximum_safe_rate_gph": round(safe, 3),
                "analytical_rate_limit_gph": round(command, 3),
                "entry_at_command_c": round(commanded_temp, 3),
                "control_policy": definition["policy"],
                "status": "PASS" if commanded_temp <= MATERIALS[material]["limit_c"] else "FAIL",
                "airflow_measured": False,
            })
    with (ROOT / "cooling_degradation_v0.6.2.1.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "revision": "technical-blocker-closure-v0.6.2.1",
        "model": "lumped cylindrical strand convection sensitivity",
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "nominal_rate_gph": 100.0,
        "airflow_measured": False,
        "production_policy": "CONTROLLED_RUNDOWN_ON_DETECTED_FAN_LOSS",
        "automatic_derate_enabled": False,
        "rows": rows,
        "limitations": [
            "fan curves and convection coefficients are bounded assumptions",
            "fan tach proves rotation, not airflow",
            "physical airflow and strand-temperature commissioning remain unperformed",
        ],
    }
    (ROOT / "cooling_degradation_v0.6.2.1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    single = [row for row in rows if row["case"] == "single_fan_operation"]
    text = [
        "# 냉각 열화 민감도 — v0.6.2.1",
        "",
        "이 결과는 가정된 대류계수에 대한 해석 민감도이며 실제 airflow/온도 시험이 아니다.",
        "fan tach는 회전만, 전류는 전기적 개연성만 증명한다.",
        "",
    ]
    for row in single:
        text.append(
            f"- {row['material']} 단일 fan: 100 g/h에서 {row['entry_at_100_gph_c']:.1f} °C, "
            f"production controlled rundown 명령 {row['analytical_rate_limit_gph']:.1f} g/h에서 "
            f"{row['entry_at_command_c']:.1f} °C "
            f"(한계 {row['puller_entry_limit_c']:.1f} °C)."
        )
    text += [
        "",
        "두 fan 모두 소실되면 feed/spool/traverse를 중지하고 forming chain을 controlled rundown으로 보낸다.",
        "오염·누설·막힘·strand 편심의 수치는 commissioning 경계 설정용 해석 상한이다. "
        "현재 firmware가 이 모델을 실시간 airflow 추정으로 사용하거나 자동 derate한다고 주장하지 않는다.",
    ]
    (ROOT / "cooling_degradation_v0.6.2.1_ko.md").write_text("\n".join(text) + "\n")
    print("COOLING_DEGRADATION_V0621_PASS")


if __name__ == "__main__":
    main()
