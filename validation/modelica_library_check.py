#!/usr/bin/env python3
"""Audit Modelica Standard Library use and CAD parameter-bridge integrity."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "simulation/openmodelica/PLA_PET_Recycler"
REV = "solid-manifold-openmodelica-v0.4"


def main() -> None:
    files = {path.relative_to(BASE).as_posix(): path.read_text() for path in BASE.rglob("*.mo")}
    joined = "\n".join(files.values())
    required = {
        "Modelica.Mechanics.Rotational": ("Components/CutterRotor.mo", "Components/ScrewDrive.mo", "Components/ChainReduction.mo", "Components/PhaseGearPair.mo", "Components/Puller.mo"),
        "Modelica.Mechanics.Translational": ("Components/FilamentSpan.mo",),
        "Modelica.Mechanics.MultiBody": ("Components/Dancer.mo", "Components/FrameMount.mo"),
    }
    for library, rels in required.items():
        assert library in joined, f"missing MSL library {library}"
        for rel in rels:
            assert library in files[rel], f"{rel} does not use {library}"
    assert "ElastoBacklash" in files["Components/ChainReduction.mo"]
    assert "ElastoBacklash" in files["Components/PhaseGearPair.mo"]
    assert "rightToothAngle" in files["Systems/ShredderSystem.mo"] and "leftToothAngle" in files["Systems/ShredderSystem.mo"]

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
    print("MODELICA_MSL_CAD_BRIDGE_OK rotational=5 translational=1 multibody=2")


if __name__ == "__main__":
    main()
