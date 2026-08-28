#!/usr/bin/env python3
"""Bridge final FreeCAD solid mass properties into OpenModelica constants."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
COMPACT=ROOT/"cad/freecad/compact"
sys.path.insert(0,str(COMPACT))

from geometry import assembly_objects, cutter_shaft, hook_disc, spur_phase_gear  # noqa: E402
from manufacturing import extruder_screw  # noqa: E402

REV="solid-manifold-openmodelica-v0.4"
DENSITY_KG_MM3={"steel":7.85e-6,"aluminum":2.70e-6,"polymer":1.20e-6,"mixed":4.0e-6}


def matrix(shape,density):
    m=shape.MatrixOfInertia
    scale=density*1e-6
    return [[getattr(m,f"A{i}{j}")*scale for j in range(1,4)] for i in range(1,4)]


def props(shape,density):
    if shape.ShapeType != "Solid" and len(shape.Solids)==1:
        shape=shape.Solids[0]
    c=shape.CenterOfMass
    return {"mass_kg":shape.Volume*density,"center_of_mass_m":[c.x/1000,c.y/1000,c.z/1000],"inertia_com_kg_m2":matrix(shape,density)}


def density_for(material):
    text=material.lower()
    if any(k in text for k in ("steel","s45c","tool","stainless","bearing","metal")): return DENSITY_KG_MM3["steel"]
    if any(k in text for k in ("al profile","aluminum","sheet")): return DENSITY_KG_MM3["aluminum"]
    if any(k in text for k in ("pla","abs","filament")): return DENSITY_KG_MM3["polymer"]
    return DENSITY_KG_MM3["mixed"]


def main():
    params=json.loads((ROOT/"cad/parameters/baseline.json").read_text())
    cutter=hook_disc(); shaft=cutter_shaft(); gear=spur_phase_gear(module=3,teeth=16,thickness=18,bore=20.2); screw=extruder_screw(2.0)
    cutter_p=props(cutter,DENSITY_KG_MM3["steel"]); shaft_p=props(shaft,DENSITY_KG_MM3["steel"]); gear_p=props(gear,DENSITY_KG_MM3["steel"]); screw_p=props(screw,DENSITY_KG_MM3["steel"])
    rotor_mass=6*cutter_p["mass_kg"]+shaft_p["mass_kg"]+gear_p["mass_kg"]
    rotor_iyy=6*cutter_p["inertia_com_kg_m2"][1][1]+shaft_p["inertia_com_kg_m2"][1][1]+gear_p["inertia_com_kg_m2"][1][1]
    items=[]
    for item in assembly_objects():
        p=props(item["shape"],density_for(item["material"])); p.update({"name":item["name"],"classification":item["classification"]}); items.append(p)
    total_mass=sum(i["mass_kg"] for i in items)
    com=[sum(i["mass_kg"]*i["center_of_mass_m"][axis] for i in items)/total_mass for axis in range(3)]
    baseline_hash=hashlib.sha256((ROOT/"cad/parameters/baseline.json").read_bytes()).hexdigest()
    p35=9.525/1000
    result={
        "revision":REV,"baseline_sha256":baseline_hash,"units":{"length":"m","mass":"kg","inertia":"kg.m2"},
        "cutter_disc":cutter_p,"cutter_shaft":shaft_p,"phase_gear":gear_p,"screw":screw_p,
        "cutter_rotor":{"mass_kg":rotor_mass,"polar_inertia_kg_m2":rotor_iyy},
        "shaft_centers_m":[[0.105,0.0,0.590],[0.153,0.0,0.590]],
        "bearing_centers_m":[[x,y,z] for x in (0.105,0.153) for y in (0.315,0.455) for z in (0.590,)],
        "cutter_sprocket_pitch_radius_m":p35/(2*math.sin(math.pi/24)),
        "motor_sprocket_pitch_radius_m":p35/(2*math.sin(math.pi/12)),
        "phase_gear_pitch_radius_m":0.003*16/2,
        "spool":{"empty_mass_kg":0.35,"full_mass_kg":1.35,"core_radius_m":0.026,"full_radius_m":0.100,"empty_inertia_kg_m2":0.5*0.35*(0.026**2+0.100**2),"full_inertia_kg_m2":0.5*1.35*(0.026**2+0.100**2)},
        "assembly":{"mass_kg":total_mass,"center_of_mass_m":com,"object_count":len(items)},
        "source_status":"CAD_SOLID_MASS_PROPERTIES",
    }
    out=ROOT/"simulation/openmodelica/generated"; out.mkdir(parents=True,exist_ok=True)
    (out/"cad_mass_properties.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    constants=f'''package CADParameters
  constant String revision = "{REV}";
  constant String baselineSHA256 = "{baseline_hash}";
  constant Real cutterDiscMass = {cutter_p['mass_kg']:.12g} "kg";
  constant Real cutterRotorMass = {rotor_mass:.12g} "kg";
  constant Real cutterRotorJ = {rotor_iyy:.12g} "kg.m2";
  constant Real screwMass = {screw_p['mass_kg']:.12g} "kg";
  constant Real screwJ = {screw_p['inertia_com_kg_m2'][2][2]:.12g} "kg.m2";
  constant Real cutterSprocketRadius = {result['cutter_sprocket_pitch_radius_m']:.12g} "m";
  constant Real motorSprocketRadius = {result['motor_sprocket_pitch_radius_m']:.12g} "m";
  constant Real phaseGearRadius = {result['phase_gear_pitch_radius_m']:.12g} "m";
  constant Real spoolEmptyJ = {result['spool']['empty_inertia_kg_m2']:.12g} "kg.m2";
  constant Real spoolFullJ = {result['spool']['full_inertia_kg_m2']:.12g} "kg.m2";
  constant Real assemblyMass = {total_mass:.12g} "kg";
  constant Real assemblyCOM[3] = {{{com[0]:.12g},{com[1]:.12g},{com[2]:.12g}}};
end CADParameters;
'''
    (out/"CADParameters.mo").write_text("within PLA_PET_Recycler.Generated;\n"+constants)
    (out/"package.mo").write_text("within PLA_PET_Recycler; package Generated end Generated;\n")
    # OpenModelica requires nested package files to live under the parent
    # package directory. This mirror is generated in the same transaction;
    # validation compares its constants with the JSON/external bridge.
    mirror=ROOT/"simulation/openmodelica/PLA_PET_Recycler/Generated.mo"
    mirror.write_text("within PLA_PET_Recycler;\npackage Generated\n"+constants+"end Generated;\n")
    print(f"CAD_TO_MODELICA_PARAMETER_SYNC_OK mass_kg={total_mass:.3f} rotor_J={rotor_iyy:.6g}")


if __name__=="__main__": main()
