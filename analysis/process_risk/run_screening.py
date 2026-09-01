#!/usr/bin/env python3
"""v0.6.2 비-Fusion 공정위험의 결정적 reduced-order screening.

실물 chip size, hopper flow, airflow를 검증하지 않는다. 범위/민감도와 Gate-2에서
확인할 실패모드만 정량화한다.
"""

from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RNG = random.Random(6202)
N = 12000


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(fraction * len(ordered)))]


def shredder() -> tuple[list[dict], dict]:
    rows: list[dict] = []
    summary: dict[str, dict] = {}
    for material, aspect_range, friction_range in (
        ("PLA", (1.2, 5.0), (0.25, 0.55)),
        ("PET", (2.0, 12.0), (0.30, 0.65)),
    ):
        escape = bridge = recirculation = axial = cycles_sum = 0.0
        for _ in range(N):
            width = RNG.uniform(2.0, 9.0)
            aspect = RNG.uniform(*aspect_range)
            friction = RNG.uniform(*friction_range)
            fill = RNG.uniform(0.15, 0.75)
            orientation = RNG.random()
            # 5 mm screen: long ribbons can align and pass; this is a screening
            # probability, not a fracture/chip-size model.
            passes = width <= 5.0 or (width <= 6.5 and orientation < 0.16 / aspect)
            ribbon = material == "PET" and aspect >= 6.0 and passes
            p_bridge = min(0.95, 0.04 + 0.42 * fill + 0.32 * friction + 0.025 * aspect)
            p_axial = min(0.8, 0.03 + 0.06 * aspect + 0.18 * fill)
            pass_probability = max(0.03, (0.62 if passes else 0.12) * (1.0 - 0.55 * p_bridge))
            cycles = min(25.0, 1.0 / pass_probability)
            escape += 1.0 if ribbon else 0.0
            bridge += p_bridge
            axial += p_axial
            recirculation += 1.0 - pass_probability
            cycles_sum += cycles
        result = {
            "material": material,
            "oversize_recirculation_probability": recirculation / N,
            "pet_ribbon_escape_probability": escape / N if material == "PET" else 0.0,
            "screen_bridging_probability": bridge / N,
            "axial_migration_probability": axial / N,
            "mean_residence_cycles": cycles_sum / N,
        }
        summary[material] = result
        rows.append(result)
    return rows, summary


def feed() -> dict:
    result: dict[str, dict] = {}
    for material, density_range, aspect_range, friction_range in (
        ("PLA", (220.0, 480.0), (1.2, 5.0), (0.25, 0.55)),
        ("PET", (180.0, 420.0), (2.0, 10.0), (0.30, 0.65)),
    ):
        throughputs: list[float] = []
        starved = 0
        bridges: list[float] = []
        for _ in range(N):
            density = RNG.uniform(*density_range)
            aspect = RNG.uniform(*aspect_range)
            friction = RNG.uniform(*friction_range)
            fill = RNG.uniform(0.35, 0.85)
            pickup = RNG.uniform(0.45, 0.90)
            bridge_probability = min(0.95, 0.03 + 0.035 * aspect + 0.45 * friction + 0.22 * (1.0 - fill))
            effective_pickup = pickup * (1.0 - 0.65 * bridge_probability)
            throughput = 100.0 * (density / 330.0) * (fill / 0.60) * (effective_pickup / 0.55)
            throughputs.append(throughput)
            bridges.append(bridge_probability)
            starved += throughput < 70.0
        result[material] = {
            "throughput_p05_g_h": percentile(throughputs, 0.05),
            "throughput_median_g_h": percentile(throughputs, 0.50),
            "throughput_p95_g_h": percentile(throughputs, 0.95),
            "starvation_probability_below_70_g_h": starved / N,
            "mean_bridge_probability": sum(bridges) / N,
            "nominal_claim_g_h": 100.0,
        }
    return result


def airflow_case(name: str, fans: int, fouling: float, leakage: float, position_factor: float) -> dict:
    flows: list[float] = []
    cooling_ratios: list[float] = []
    for _ in range(N // 4):
        free_flow_single = RNG.uniform(20.0, 40.0)  # m3/h assumption, donor not identified
        shutoff_pa = RNG.uniform(80.0, 140.0)
        system_k = RNG.uniform(0.08, 0.18) * fouling / max(0.35, 1.0 - leakage)
        free_flow = free_flow_single * fans
        if fans == 0:
            flow = 0.0
        else:
            # shutoff*(1-Q/Qfree)^2 = K*Q^2, positive analytic root
            flow = math.sqrt(shutoff_pa) / (math.sqrt(system_k) + math.sqrt(shutoff_pa) / free_flow)
        flow *= position_factor
        flows.append(flow)
        cooling_ratios.append((max(flow, 0.01) / 35.0) ** 0.60)
    return {
        "case": name,
        "fan_count": fans,
        "flow_p05_m3_h": percentile(flows, 0.05),
        "flow_median_m3_h": percentile(flows, 0.50),
        "flow_p95_m3_h": percentile(flows, 0.95),
        "relative_heat_transfer_median": percentile(cooling_ratios, 0.50),
        "airflow_is_measured": False,
    }


def airflow() -> list[dict]:
    return [
        airflow_case("dual_fan_clean_centered", 2, 1.0, 0.05, 1.0),
        airflow_case("single_fan_loss", 1, 1.0, 0.05, 1.0),
        airflow_case("filter_fouling", 2, 1.8, 0.05, 1.0),
        airflow_case("duct_leakage", 2, 1.0, 0.30, 0.9),
        airflow_case("strand_position_edge", 2, 1.0, 0.05, 0.72),
        airflow_case("dual_fan_loss", 0, 1.0, 0.05, 1.0),
    ]


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    shred_rows, shred_summary = shredder()
    feed_summary = feed()
    airflow_rows = airflow()
    with (ROOT / "shredder_particle_sensitivity.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(shred_rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(shred_rows)
    with (ROOT / "cooling_airflow_sensitivity.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(airflow_rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(airflow_rows)
    shred_risk = "MITIGATION_REQUIRED" if any(
        row["screen_bridging_probability"] > 0.35 or row["pet_ribbon_escape_probability"] > 0.02
        for row in shred_rows) else "LOW_RISK"
    (ROOT / "shredder_particle_screening.md").write_text(f"""# Shredder particle screening — v0.6.2

- 판정: `{shred_risk}`
- 방법: 12,000개/재료 seeded Monte Carlo reduced-order contact/transport screening
- 경계조건: 5 mm screen, width 2–9 mm, 재료별 aspect ratio·wall friction·fill 범위
- PLA: oversize recirculation {shred_summary['PLA']['oversize_recirculation_probability']:.1%}, bridging {shred_summary['PLA']['screen_bridging_probability']:.1%}, mean residence {shred_summary['PLA']['mean_residence_cycles']:.2f} cycles
- PET: oversize recirculation {shred_summary['PET']['oversize_recirculation_probability']:.1%}, ribbon escape {shred_summary['PET']['pet_ribbon_escape_probability']:.1%}, bridging {shred_summary['PET']['screen_bridging_probability']:.1%}, mean residence {shred_summary['PET']['mean_residence_cycles']:.2f} cycles
- 완화: removable screen inspection/cleaning, ribbon-rich feed 배제, Gate-2 회수율·bridging coupon 시험
- 한계: fracture-calibrated DEM이 아니며 실제 chip size·통과율을 검증하지 않는다. granulator 추가는 architecture freeze 때문에 자동 제안/적용하지 않는다.
""", encoding="utf-8")
    lines = ["# Hopper/screw feed screening — v0.6.2", "", "100 g/h는 nominal claim으로 유지하며 모델 결과로 상향하지 않는다.", ""]
    for material, row in feed_summary.items():
        lines.append(f"- {material}: throughput P05/median/P95 = {row['throughput_p05_g_h']:.1f}/{row['throughput_median_g_h']:.1f}/{row['throughput_p95_g_h']:.1f} g/h; starvation(<70 g/h) {row['starvation_probability_below_70_g_h']:.1%}; mean bridge probability {row['mean_bridge_probability']:.1%}")
    lines += ["", "입력 범위는 bulk density, aspect ratio, wall friction, fill factor, pickup efficiency다. 실측 bulk density/flow coupon 전에는 `MODEL_INSUFFICIENT`이며 starvation 검출용 screw tach와 feeder interlock을 유지한다."]
    (ROOT / "hopper_screw_feed_screening.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    worst = next(row for row in airflow_rows if row["case"] == "single_fan_loss")
    (ROOT / "cooling_airflow_sensitivity.md").write_text(f"""# Cooling airflow sensitivity — v0.6.2

- 방법: assumed fan curve와 quadratic duct pressure-drop network, seeded parameter sweep
- single-fan-loss median flow: {worst['flow_median_m3_h']:.1f} m³/h
- topology: fan electrical feedback(A4)는 전기적 부하만, mux된 fan tach는 회전만 증명한다.
- airflow inference: fan curve/duct model 출력이며 실제 airflow가 아니다.
- actual airflow: 미측정. duct blockage, filter fouling, leakage, strand 위치는 별도 sensitivity case다.
- 제어 연결: 상대 heat-transfer coefficient는 `(Q/35)^0.60`으로 기존 cooling time scale에만 연결한다. 단일 fan 손실은 실제 firmware에서 forming-chain fault다.
""", encoding="utf-8")
    summary = {
        "revision": "parallel-actuation-hardening-v0.6.2",
        "method": "seeded reduced-order screening",
        "sample_count_per_material": N,
        "shredder_classification": shred_risk,
        "feed_classification": "MODEL_INSUFFICIENT",
        "airflow_classification": "MITIGATION_REQUIRED",
        "shredder": shred_summary,
        "feed": feed_summary,
        "airflow": airflow_rows,
        "claims_excluded": ["actual chip size", "actual mass flow", "actual airflow", "production reliability"],
    }
    (ROOT / "process_risk_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print("PROCESS_RISK_SCREENING_OK")


if __name__ == "__main__":
    main()
