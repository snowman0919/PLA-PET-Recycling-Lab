#!/usr/bin/env python3
"""Quantified two-tower architecture contract and stability screening.

The model locks layout envelopes without pretending that unknown donor masses,
profile joints, table anchors or vibration spectra have been physically proved.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
G = 9.80665


TOWER_A_MODULES = (
    ("sealed_batch_bin_full", 4.0, 95.0),
    ("vibratory_sorter", 5.0, 294.0),
    ("stage3_granulator", 7.0, 507.5),
    ("stage2_shredder", 8.0, 717.5),
    ("stage1_shredder", 12.0, 942.5),
    ("input_classifier", 3.5, 1210.0),
    ("frame_shelves_guards", 18.0, 675.0),
)

TOWER_B_MODULES = (
    ("extruder_hot_zone", 25.0, 230.0),
    ("spooler_full", 6.35, 300.0),
    ("forming_service_rail", 6.0, 520.0),
    ("control_enclosure", 8.0, 650.0),
    ("dryer_feeder_full", 12.0, 820.0),
    ("frame_shelves_guards", 18.0, 575.0),
)


def mass_properties(modules: tuple[tuple[str, float, float], ...]) -> dict[str, float]:
    mass = sum(item[1] for item in modules)
    cg_z = sum(item[1] * item[2] for item in modules) / mass
    return {"estimated_operating_mass_kg": mass, "estimated_vertical_cg_mm": cg_z}


def tipping_screen(
    modules: tuple[tuple[str, float, float], ...],
    base_depth_mm: float,
    operating_acceleration_g: float,
    point_force_n: float,
    point_force_height_mm: float,
    dynamic_factor: float,
    anchor_spacing_mm: float,
) -> dict[str, float | bool]:
    props = mass_properties(modules)
    mass = props["estimated_operating_mass_kg"]
    cg_m = props["estimated_vertical_cg_mm"] / 1000
    half_base_m = base_depth_mm / 2000
    weight = mass * G
    inertial_force = mass * G * operating_acceleration_g
    overturning = dynamic_factor * (
        inertial_force * cg_m + point_force_n * point_force_height_mm / 1000
    )
    restoring = weight * half_base_m
    anchor_pair_tension = max(0.0, overturning - restoring) / (anchor_spacing_mm / 1000)
    unanchored_tip_acceleration_g = half_base_m / cg_m
    return {
        **props,
        "operating_acceleration_g": operating_acceleration_g,
        "unanchored_tip_acceleration_g": unanchored_tip_acceleration_g,
        "unanchored_margin_over_operating": unanchored_tip_acceleration_g / operating_acceleration_g,
        "factored_overturning_moment_nm": overturning,
        "gravity_restoring_moment_nm": restoring,
        "required_anchor_pair_tension_n": anchor_pair_tension,
        "anchor_candidate_per_point_pullout_n": 1000.0,
        "anchor_candidate_safety_factor": 2000.0 / max(anchor_pair_tension, 1e-9),
        "anchor_required": anchor_pair_tension > 0,
    }


def build_report() -> dict:
    tower_a_stability = tipping_screen(
        TOWER_A_MODULES,
        base_depth_mm=600.0,
        operating_acceleration_g=0.35,
        point_force_n=60.0,
        point_force_height_mm=942.5,
        dynamic_factor=1.5,
        anchor_spacing_mm=520.0,
    )
    tower_b_stability = tipping_screen(
        TOWER_B_MODULES,
        base_depth_mm=600.0,
        operating_acceleration_g=0.10,
        point_force_n=80.0,
        point_force_height_mm=230.0,
        dynamic_factor=1.5,
        anchor_spacing_mm=520.0,
    )
    usable_bin_l = 6.0
    bulk_density_kg_m3 = 250.0
    flake_capacity_kg = usable_bin_l / 1000 * bulk_density_kg_m3

    return {
        "status": "ARCHITECTURE_CONTRACT_VIRTUAL_EVIDENCE_PHYSICAL_REVIEW_OPEN",
        "requirement_resolution": {
            "release_configuration": {
                "shredding": "THREE_STAGE_REQUIRED",
                "classification": "PLA_PET_UNKNOWN_PLUS_FIXED_SIX_COLOR_AND_REJECT",
                "reason": "The original user goal explicitly makes three-stage shredding and fixed color routing final acceptance requirements.",
            },
            "commissioning_comparison_only": {
                "shredding": "STAGE_3_BYPASS_ALLOWED_FOR_COUPON_COMPARISON",
                "classification": "MATERIAL_PLUS_REJECT_ROUTING_ALLOWED_DURING_DATASET_BRINGUP",
                "restriction": "Comparison modes may not remove release hardware or close final functional requirements.",
            },
        },
        "tower_a": {
            "role": "classification_shredding_sorting_batch_storage",
            "rack_envelope_mm": {"width": 600.0, "depth": 600.0, "height": 1350.0},
            "maximum_input_lip_height_from_floor_mm": 1320.0,
            "primary_profile": "4040",
            "secondary_shelf_profile": "2040",
            "module_order_bottom_to_top": [item[0] for item in TOWER_A_MODULES[:-1]],
            "stability_screen": tower_a_stability,
            "anchor_pattern_mm": {"x": 520.0, "y": 520.0, "points": 4},
        },
        "tower_b": {
            "role": "drying_extrusion_forming_spooling_controls",
            "rack_envelope_mm": {"width": 900.0, "depth": 600.0, "height": 1150.0},
            "straight_service_rail_extension_from_die_mm": 760.0,
            "overall_operating_envelope_with_rail_mm": {
                "length": 1660.0,
                "depth": 600.0,
                "height": 1150.0,
            },
            "cooling_length_mm": 440.0,
            "die_to_gauge_center_mm": 470.0,
            "puller_start_from_die_mm": 600.0,
            "spooler_layout": "offset_beside_rail_end_without_bending_hot_strand",
            "primary_profile": "4040",
            "service_rail_profile": "2040",
            "stability_screen": tower_b_stability,
            "anchor_pattern_mm": {"x": 820.0, "y": 520.0, "points": 4},
        },
        "batch_interface": {
            "transfer": "manual_sealed_removable_bin",
            "gross_volume_l": 8.0,
            "usable_volume_l": usable_bin_l,
            "design_bulk_density_kg_m3": bulk_density_kg_m3,
            "nominal_flake_capacity_kg": flake_capacity_kg,
            "maximum_handled_mass_kg": 2.0,
            "docking": "asymmetric_key_plus_two_captive_M5_clamps_and_sealed_metal_throat",
            "identity": "machine_read_batch_id_plus_material_color_lot_label",
            "contamination_gate": "closed_gate_before_undock_and_visible_cleanliness_check_before_redock",
        },
        "safety_zones": {
            "common": "one_latching_estop_chain_removes hazardous energy in both towers",
            "tower_a": "separate monitored contactor for shredder and sorter hazardous motion",
            "tower_b": "separate monitored contactor for drive and fused heater branches",
            "control_enclosure": "one common grounded enclosure on Tower B lower rear",
            "maintenance": "one tower may remain logic-powered only; hazardous energy cannot follow a batch-bin or data connection",
            "external_credit": "workshop safety hardware may be credited only after model rating channel and fault-test inventory",
        },
        "mandatory_physical_gates": [
            "Confirm floor/workbench anchor substrate and achieve at least 1 kN pullout per point with the selected fastener system.",
            "Measure final module masses and center of gravity; rerun the model before powered motion.",
            "Verify maximum input lip height against the actual operator and refill container.",
            "Run sorter and shredder vibration/coast-down tests while logging both tower and optical-rail acceleration.",
            "Prove every chute boot and batch-bin docking path can be removed and cleaned without opening a cutter guard.",
        ],
        "model_limits": [
            "Module masses are conservative planning estimates, not donor measurements.",
            "Rigid-body tipping does not model profile-joint compliance, floor flexibility, resonance, impact or anchor edge distance.",
            "The straight forming rail is retained because hot filament bend radius and solidification are not physically validated.",
        ],
    }


def markdown(report: dict) -> str:
    a = report["tower_a"]
    b = report["tower_b"]
    ai = a["stability_screen"]
    bi = b["stability_screen"]
    batch = report["batch_interface"]
    return f"""# 2‑tower 수치 아키텍처 계약

상태: **ARCHITECTURE CONTRACT / VIRTUAL EVIDENCE / PHYSICAL REVIEW OPEN**

이 문서는 기존 2,295×520×720 mm 직선 proof를 다음 revision의 제작 승인본으로 사용하지 않고, 두 rack의 치수·기능·안전 경계를 고정한다. 원문 최종 합격기준과 최신 최소화 방향이 충돌하는 부분은 최종 기능을 삭제하지 않는 쪽으로 해결했다.

## 범위 결정

- Release 구성은 **3단 파쇄**, PLA/PET/UNKNOWN, 고정 6색+Reject를 유지한다.
- Stage 3 bypass와 material+Reject routing은 coupon/dataset commissioning 비교 모드일 뿐이다. Hardware/BOM을 삭제하거나 최종 요구사항을 닫는 근거로 쓰지 않는다.
- Tower 간 이송은 자동 docking 대신 밀폐 수동 batch bin을 사용한다.

## 고정 envelope

| 항목 | Tower A | Tower B |
|---|---:|---:|
| 역할 | 분류·3단 파쇄·선별·batch | 건조·압출·성형·권취·제어 |
| Rack | 600×600×1350 mm | 900×600×1150 mm |
| 추가 rail | 없음 | die 이후 760 mm |
| 운전 envelope | 600×600×1350 mm | 1660×600×1150 mm |
| 추정 운전 질량 | {ai['estimated_operating_mass_kg']:.2f} kg | {bi['estimated_operating_mass_kg']:.2f} kg |
| 추정 수직 CG | {ai['estimated_vertical_cg_mm']:.1f} mm | {bi['estimated_vertical_cg_mm']:.1f} mm |
| 무고정 tip 가속도 | {ai['unanchored_tip_acceleration_g']:.3f} g | {bi['unanchored_tip_acceleration_g']:.3f} g |
| 계산 anchor pair tension | {ai['required_anchor_pair_tension_n']:.1f} N | {bi['required_anchor_pair_tension_n']:.1f} N |

Tower A는 0.35 g sorter 전달목표와 60 N cutter 반력을 1.5배 한 rigid-body screen에서 중력 복원모멘트를 넘으므로 **4점 anchor가 필수**다. 각 점 1 kN pullout 후보는 실제 substrate, edge distance와 fastener 시험으로 확정한다. Tower B도 공통 설치정책상 4점 고정한다.

## Batch·공정 interface

- Bin: gross {batch['gross_volume_l']:.1f} L, usable {batch['usable_volume_l']:.1f} L, 250 kg/m³에서 {batch['nominal_flake_capacity_kg']:.1f} kg, 취급상한 2.0 kg.
- 비대칭 key + captive M5 clamp 2개 + sealed metal throat를 사용한다.
- Gate를 닫기 전 undock 금지, redock 전 가시 청결검사, batch ID/material/color/lot 추적을 요구한다.
- Tower B는 cooling 440 mm, die→gauge 470 mm, puller 시작 600 mm를 유지한다. Hot strand를 꺾어 footprint를 줄이지 않는다.

## 안전 경계

- 공통 latching E-stop chain은 두 tower의 위험에너지를 모두 제거한다.
- Tower A motion과 Tower B drive/heater는 별도 monitored contactor/branch로 분리한다.
- 공통 접지 제어함 1개를 Tower B 하부 뒤쪽에 둔다.
- Batch/data connector로 다른 tower의 위험에너지가 따라 켜지지 않는다.
- 작업실 보유 안전장비는 model/rating/channel/fault test가 inventory된 뒤에만 credit한다.

## 미완료 gate

질량·CG 실측, anchor pullout, operator reach, profile joint/선반, modal/진동, chute cleaning, guard/service path는 물리 검증 전 열려 있다. 상세 수치와 가정은 `simulation/architecture/two_tower_contract.json`에 있다.
"""


def main() -> None:
    report = build_report()
    simulation = ROOT / "simulation" / "architecture"
    simulation.mkdir(parents=True, exist_ok=True)
    (simulation / "two_tower_contract.json").write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "requirements" / "architecture_contract.md").write_text(markdown(report))
    print(json.dumps(report, indent=2))
    print("TWO_TOWER_ARCHITECTURE_CONTRACT_OK")


if __name__ == "__main__":
    main()
