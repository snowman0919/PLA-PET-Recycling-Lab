#!/usr/bin/env python3
"""Generate the deterministic OpenModelica scenario runner from acceptance criteria."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CRITERIA = json.loads((ROOT / "simulation/openmodelica/acceptance_criteria.json").read_text())


def duration(name: str) -> tuple[int, int]:
    if name == "GaugeDropout": return 140, 2800
    if name == "PullerSaturation": return 100, 2000
    if name == "OvalityDisturbance": return 100, 2000
    if name == "ThermalFuseLongDuration": return 14400, 3600
    if name in {"MOSFETStuckOn"}: return 7200, 3600
    if name.startswith("HotExtrusionJam"): return 2400, 2400
    if name.startswith("ReliefOpening"): return 2400, 2400
    if name.startswith("Extruder") or name.startswith("Heater"): return 1800, 1800
    if name.startswith("FullSystem"):
        return (1800, 1800) if name in {"FullSystemPLA", "FullSystemPET", "FullSystemGaugeFailure"} else (20, 1000)
    if name in {"GaugeFailureControlledPause", "FeederLossDuringExtrusion", "CoolingLossDuringExtrusion", "SpoolerPermissionLoss"}: return 1800, 1800
    if name in CRITERIA["scenario_groups"].get("purge", []): return 2200, 2200
    if name == "PurgeNormalAbortCooldown": return 7, 700
    if name == "PurgeSuccessfulCompletionCooldown": return 500, 1000
    if name == "GaugeRequalification": return 2150, 4300
    if name == "QualityViolationRequalification": return 45, 900
    if name in {"GaugeLossRundown", "CoolingLossRundown", "SpoolPermissionLossRundown"}: return 1700, 3400
    if name in {"PullerTachStartupGrace", "PullerTachStartupFailure"}: return 8, 800
    if name in CRITERIA["scenario_groups"]["shredder"]: return 18, 1800
    if name in CRITERIA["scenario_groups"]["forming"]: return 60, 1200
    if name in CRITERIA["scenario_groups"]["spool"]: return 12, 1200
    if name in {"PreheatRejectsInvalidCoolingFeedback", "PreheatCoolingStartupProbe", "PreheatCoolingProbeDropout", "PurgeCoolingStartupProbe"}: return 7, 700
    return 5, 500


def main() -> None:
    lines = [
        'loadFile(getInstallationDirectoryPath()+"/share/omlibrary/libraries/Complex 4.0.0/package.mo");',
        'loadFile(getInstallationDirectoryPath()+"/share/omlibrary/libraries/ModelicaServices 4.0.0/package.mo");',
        'loadFile(getInstallationDirectoryPath()+"/share/omlibrary/libraries/Modelica 4.0.0/package.mo");',
        'loadFile("simulation/openmodelica/PLA_PET_Recycler/package.mo");',
        'cd("simulation/openmodelica/results/raw");',
    ]
    for name in CRITERIA["required_scenarios"]:
        stop, intervals = duration(name)
        lines.append(f'simulate(PLA_PET_Recycler.Scenarios.{name},startTime=0,stopTime={stop},numberOfIntervals={intervals},tolerance=1e-6,method="dassl",outputFormat="csv",fileNamePrefix="{name}");')
    lines.append("getErrorString();")
    (ROOT / "simulation/openmodelica/scripts/run_all.mos").write_text("\n".join(lines) + "\n")
    print(f"MODELICA_RUNNER_SYNC_OK scenarios={len(CRITERIA['required_scenarios'])}")


if __name__ == "__main__":
    main()
