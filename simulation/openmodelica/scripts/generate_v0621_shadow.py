#!/usr/bin/env python3
"""Generate the v0.6.2.1 OpenModelica shadow contract and runner.

The generated constants bind the reduced-order shadow to the same machine-readable
tach, actuator, feed, and recirculation inputs consumed by the production lanes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCENARIOS = ROOT / "simulation/openmodelica/PLA_PET_Recycler/Scenarios"
RESULTS = ROOT / "simulation/openmodelica/results_v0.6.2.1"

P0K_SCENARIOS = [
    "LowSpeedTachShredder",
    "LowSpeedTachScrew",
    "LowSpeedTachPuller",
    "LowSpeedTachSpooler",
    "TachJitter",
    "TachMissingPulse",
    "TachRollover",
    "ShredderClosedLoopLoadStep",
    "ScrewClosedLoopPressureStep",
    "PullerClosedLoopLowSpeed",
    "SpoolerClosedLoopEmptyToFull",
    "TraverseHomeMiddle",
    "TraverseHomeWrongDirection",
    "TraverseLimitFailure",
    "PLAShredderRecirculation",
    "PETRibbonRecirculation",
    "PLAHopperBridgeClear",
    "PETHopperBridgeClear",
    "FeedRateNominalPLA",
    "FeedRateNominalPET",
    "FeedRateDegradedSafePause",
]

# P0-K enumerates 21 names. These three P0-C regressions complete the requested
# 24-case shadow suite without pretending they were separately named by P0-K.
EXTRA_CONTROL_SCENARIOS = [
    "ActuatorDeadZoneRecovery",
    "ActuatorSaturationRecovery",
    "ActuatorTachLossRundown",
]
SCENARIOS_ALL = P0K_SCENARIOS + EXTRA_CONTROL_SCENARIOS

SOURCES = {
    "tach_contract": ROOT / "control/tach_contract.json",
    "drive_contract": ROOT / "control/drive_actuation_contract_v0.6.2.1.json",
    "feed_parameters": ROOT / "analysis/process_feed/feed_parameters.json",
    "feed_validation": ROOT / "analysis/process_feed/feed_validation.json",
    "recirculation_parameters": ROOT / "analysis/shredder_recirculation/recirculation_parameters.json",
    "recirculation_validation": ROOT / "analysis/shredder_recirculation/recirculation_validation.json",
    "frozen_envelope": ROOT / "analysis/load_cases/openmodelica_dynamic_envelope.json",
    "fusion_binding": ROOT / "exports/fusion_validation/run_binding.json",
    "process_fusion_delta": ROOT / "exports/process_v0621/fusion_change_classification.json",
}

EXTRA_HASH_SOURCES = {
    "scenario_model": ROOT / "simulation/openmodelica/PLA_PET_Recycler/Scenarios/V0621ShadowScenarios.mo",
    "package_order": ROOT / "simulation/openmodelica/PLA_PET_Recycler/Scenarios/package.order",
    "generator": ROOT / "simulation/openmodelica/scripts/generate_v0621_shadow.py",
    "validator": ROOT / "simulation/openmodelica/postprocess/validate_v0621_shadow.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmt(value: float | int) -> str:
    return format(float(value), ".17g")


def main() -> None:
    documents = {name: json.loads(path.read_text()) for name, path in SOURCES.items()}
    tach = {row["channel"]: row for row in documents["tach_contract"]["channels"]}
    drives = documents["drive_contract"]["drives"]
    feed_p = documents["feed_parameters"]["control"]
    feed_v = documents["feed_validation"]
    recirc_v = documents["recirculation_validation"]["worst_case"]
    frozen = documents["frozen_envelope"]

    lines = [
        "within PLA_PET_Recycler.Scenarios;",
        "package V0621Contracts",
        '  constant String revision="technical-blocker-closure-v0.6.2.1";',
    ]
    for channel, prefix in (("shredder", "shredder"), ("screw", "screw"),
                            ("puller", "puller"), ("spooler", "spooler")):
        row = tach[channel]
        lines.extend([
            f"  constant Integer {prefix}Ppr={int(row['ppr'])};",
            f"  constant Real {prefix}MinRpm={fmt(row['expected_min_rpm'])};",
            f"  constant Real {prefix}MaxRpm={fmt(row['expected_max_rpm'])};",
            f"  constant Real {prefix}CrossoverRpm={fmt(row['period_count_crossover_rpm'])};",
            f"  constant Real {prefix}TimeoutUs={fmt(row['timeout_us'])};",
            f"  constant Real {prefix}MinPulseSpacingUs={fmt(row['minimum_pulse_spacing_us'])};",
            f"  constant Real {prefix}FilterTauS={fmt(row['filter_time_constant_us'] / 1e6)};",
            f"  constant Real {prefix}MaxAccelRpmS={fmt(row['maximum_plausible_acceleration_rpm_s'])};",
        ])
    lines.extend([
        f"  constant Real shredderNormalRpm={fmt(drives['shredder']['normal_target_rpm'][1])};",
        f"  constant Real screwNormalRpm={fmt(drives['screw']['normal_target_rpm'][0])};",
        f"  constant Real pullerNormalMinRpm={fmt(drives['puller']['normal_target_rpm'][0])};",
        f"  constant Real pullerNormalMaxRpm={fmt(drives['puller']['normal_target_rpm'][1])};",
        f"  constant Real pullerControllableMinRpm={fmt(drives['puller']['required_controllable_rpm'][0])};",
        f"  constant Real pullerControllableMaxRpm={fmt(drives['puller']['required_controllable_rpm'][1])};",
        f"  constant Real pullerPwmDeadZoneFraction={fmt(drives['puller']['pwm_dead_zone'] / drives['puller']['maximum_pwm'])};",
        f"  constant Real spoolerNormalMinRpm={fmt(drives['spooler']['normal_target_rpm_empty_to_full'][0])};",
        f"  constant Real spoolerNormalMaxRpm={fmt(drives['spooler']['normal_target_rpm_empty_to_full'][1])};",
        f"  constant Real spoolerControllableMinRpm={fmt(drives['spooler']['required_controllable_rpm'][0])};",
        f"  constant Real spoolerControllableMaxRpm={fmt(drives['spooler']['required_controllable_rpm'][1])};",
        f"  constant Real feedTargetGH={fmt(feed_p['target_feed_g_h'])};",
        f"  constant Real feedNormalMinGH={fmt(feed_p['normal_min_g_h'])};",
        f"  constant Real feedNormalMaxGH={fmt(feed_p['normal_max_g_h'])};",
        f"  constant Real feedInventoryTargetG={fmt(feed_p['inventory_target_g'])};",
        f"  constant Real feedInventoryCapacityG={fmt(feed_p['inventory_capacity_g'])};",
        f"  constant Real feedTorqueLimitNm={fmt(feed_p['torque_limit_nm'])};",
        f"  constant Real feedCurrentLimitA={fmt(feed_p['current_limit_a'])};",
        f"  constant Real feedNominalMinObservedGH={fmt(feed_v['delivered_feed_range_g_h'][0])};",
        f"  constant Real feedNominalMaxObservedGH={fmt(feed_v['delivered_feed_range_g_h'][1])};",
        f"  constant Real recirculationReturnProbability={fmt(recirc_v['minimum_oversize_return_probability'])};",
        f"  constant Real ribbonBypassProbability={fmt(recirc_v['maximum_pet_ribbon_bypass_probability'])};",
        f"  constant Real deadPocketProbability={fmt(recirc_v['maximum_dead_pocket_retention_probability'])};",
        f"  constant Real axialMigrationProbability={fmt(recirc_v['maximum_axial_migration_probability'])};",
        f"  constant Real cutterEnvelopeNm={fmt(frozen['loads']['peak_cutter_torque_nm'])};",
        f"  constant Real phaseEnvelopeNm={fmt(frozen['loads']['peak_phase_torque_nm'])};",
        f"  constant Real bearingEnvelopeN={fmt(frozen['loads']['peak_bearing_load_n'])};",
        f"  constant Real chainEnvelopeN={fmt(frozen['loads']['peak_chain_force_n'])};",
        "end V0621Contracts;",
        "",
    ])
    (SCENARIOS / "V0621Contracts.mo").write_text("\n".join(lines))

    mos = [
        'loadModel(Modelica, {"4.0.0"});',
        'loadFile("simulation/openmodelica/PLA_PET_Recycler/package.mo");',
        'cd("simulation/openmodelica/results_v0.6.2.1/raw");',
    ]
    for name in SCENARIOS_ALL:
        mos.append(
            f"simulate(PLA_PET_Recycler.Scenarios.V0621ShadowScenarios.{name},"
            f'stopTime=20,numberOfIntervals=400,method="dassl",outputFormat="csv",'
            f'fileNamePrefix="{name}");'
        )
    mos.append("getErrorString();")
    (ROOT / "simulation/openmodelica/scripts/run_v0621_shadow.mos").write_text("\n".join(mos) + "\n")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "raw").mkdir(parents=True, exist_ok=True)
    manifest = {
        "revision": "technical-blocker-closure-v0.6.2.1",
        "scenario_count": len(SCENARIOS_ALL),
        "p0_k_enumerated_count": len(P0K_SCENARIOS),
        "p0_k_scenarios": P0K_SCENARIOS,
        "additional_p0_c_regressions": EXTRA_CONTROL_SCENARIOS,
        "source_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in [*SOURCES.values(), *EXTRA_HASH_SOURCES.values()]
        } | {
            "simulation/openmodelica/PLA_PET_Recycler/Scenarios/V0621Contracts.mo":
                sha256(SCENARIOS / "V0621Contracts.mo"),
            "simulation/openmodelica/scripts/run_v0621_shadow.mos":
                sha256(ROOT / "simulation/openmodelica/scripts/run_v0621_shadow.mos"),
        },
        "generated_files": [
            "simulation/openmodelica/PLA_PET_Recycler/Scenarios/V0621Contracts.mo",
            "simulation/openmodelica/scripts/run_v0621_shadow.mos",
        ],
        "classification": "VIRTUAL_SIMULATION_ONLY_PHYSICAL_TEST_NOT_RUN",
    }
    (RESULTS / "scenario_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"V0621_SHADOW_GENERATED {len(SCENARIOS_ALL)} scenarios")


if __name__ == "__main__":
    main()
