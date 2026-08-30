#!/usr/bin/env python3
"""Audit Modelica Standard Library use and CAD parameter-bridge integrity."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "simulation/openmodelica/PLA_PET_Recycler"
REV = "virtual-physics-closure-v0.5.1"


def main() -> None:
    files = {path.relative_to(BASE).as_posix(): path.read_text() for path in BASE.rglob("*.mo")}
    joined = "\n".join(files.values())
    required = {
        "Modelica.Mechanics.Rotational": ("Components/DCMotorElectrical.mo", "Components/LossyGearbox.mo", "Components/ElasticChainDrive.mo", "Components/PhaseGearMesh.mo", "Components/HookMaterialLoad.mo"),
    }
    for library, rels in required.items():
        assert library in joined, f"missing MSL library {library}"
        for rel in rels:
            assert library in files[rel], f"{rel} does not use {library}"
    assert "SmoothBacklash" in files["Components/ElasticChainDrive.mo"]
    assert "SmoothBacklash" in files["Components/PhaseGearMesh.mo"]
    assert "Modelica.Constants.pi/7" in files["Systems/CoupledShredderSystem.mo"]
    for rel in (
        "Components/DCMotorElectrical.mo", "Components/LossyGearbox.mo",
        "Components/ElasticChainDrive.mo", "Components/PhaseGearMesh.mo",
        "Components/ShearFuse.mo", "Systems/CoupledShredderSystem.mo",
        "Systems/ThermalExtruderSystem.mo", "Systems/DynamicSpoolSystem.mo",
        "Systems/FullCoupledSystem.mo",
    ):
        assert rel in files, f"coupled v0.5 model missing {rel}"

    bridge = json.loads((ROOT / "simulation/openmodelica/generated/cad_mass_properties.json").read_text())
    assert bridge["revision"] == REV and bridge["source_status"] == "CAD_SOLID_MASS_PROPERTIES"
    assert bridge["units"] == {"length": "m", "mass": "kg", "inertia": "kg.m2"}
    assert len(bridge["shaft_centers_m"]) == 2 and len(bridge["bearing_centers_m"]) == 4
    assert bridge["assembly"]["mass_kg"] > bridge["frame_base"]["mass_kg"] > 0
    expected_hash = hashlib.sha256((ROOT / "cad/parameters/baseline.json").read_bytes()).hexdigest()
    assert bridge["baseline_sha256"] == expected_hash
    generated = (ROOT / "simulation/openmodelica/PLA_PET_Recycler/Generated.mo").read_text()
    for token in (expected_hash, "shaftCenters[2,3]", "bearingCenters[4,3]", "assemblyInertia[3,3]"):
        assert token in generated, f"generated Modelica bridge missing {token}"
    print("MODELICA_MSL_CAD_BRIDGE_OK electrical=1 rotational=5")


if __name__ == "__main__":
    main()
