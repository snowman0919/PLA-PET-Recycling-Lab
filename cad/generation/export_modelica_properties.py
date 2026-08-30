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

REV="implementation-crosssolver-v0.6"
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


def aggregate(items):
    total=sum(item["mass_kg"] for item in items)
    com=[sum(item["mass_kg"]*item["center_of_mass_m"][axis] for item in items)/total for axis in range(3)]
    inertia=[[0.0]*3 for _ in range(3)]
    for item in items:
        d=[item["center_of_mass_m"][i]-com[i] for i in range(3)]; d2=sum(x*x for x in d); mass=item["mass_kg"]
        for i in range(3):
            for j in range(3):
                inertia[i][j]+=item["inertia_com_kg_m2"][i][j]+mass*((d2 if i==j else 0)-d[i]*d[j])
    return {"mass_kg":total,"center_of_mass_m":com,"inertia_com_kg_m2":inertia,"object_count":len(items)}


def main():
    params=json.loads((ROOT/"cad/parameters/baseline.json").read_text())
    cutter=hook_disc(); shaft=cutter_shaft(); gear=spur_phase_gear(module=3,teeth=16,thickness=18,bore=20.2); screw=extruder_screw(2.0)
    cutter_p=props(cutter,DENSITY_KG_MM3["steel"]); shaft_p=props(shaft,DENSITY_KG_MM3["steel"]); gear_p=props(gear,DENSITY_KG_MM3["steel"]); screw_p=props(screw,DENSITY_KG_MM3["steel"])
    rotor_mass=6*cutter_p["mass_kg"]+shaft_p["mass_kg"]+gear_p["mass_kg"]
    rotor_iyy=6*cutter_p["inertia_com_kg_m2"][1][1]+shaft_p["inertia_com_kg_m2"][1][1]+gear_p["inertia_com_kg_m2"][1][1]
    items=[]
    for item in assembly_objects():
        density=density_for(item["material"])
        if item.get("mass_override_kg") is not None:
            density=item["mass_override_kg"]/item["shape"].Volume
        p=props(item["shape"],density); p.update({"name":item["name"],"group":item["group"],"classification":item["classification"],"mass_source":"published_or_measured_override" if item.get("mass_override_kg") is not None else "solid_volume_x_material_density","evidence":item.get("evidence","")}); items.append(p)
    assembly=aggregate(items); frame=aggregate([item for item in items if item["group"]=="frame"])
    total_mass=assembly["mass_kg"]; com=assembly["center_of_mass_m"]
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
        "assembly":assembly,"frame_base":frame,
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
  constant Real shaftCenters[2,3] = [0.105,0,0.590;0.153,0,0.590] "m";
  constant Real bearingCenters[4,3] = [0.105,0.315,0.590;0.105,0.455,0.590;0.153,0.315,0.590;0.153,0.455,0.590] "m";
  constant Real spoolEmptyJ = {result['spool']['empty_inertia_kg_m2']:.12g} "kg.m2";
  constant Real spoolFullJ = {result['spool']['full_inertia_kg_m2']:.12g} "kg.m2";
  constant Real assemblyMass = {total_mass:.12g} "kg";
  constant Real assemblyCOM[3] = {{{com[0]:.12g},{com[1]:.12g},{com[2]:.12g}}};
  constant Real assemblyInertia[3,3] = [{';'.join(','.join(f'{value:.12g}' for value in row) for row in assembly['inertia_com_kg_m2'])}];
  constant Real frameMass = {frame['mass_kg']:.12g} "kg";
  constant Real frameCOM[3] = {{{frame['center_of_mass_m'][0]:.12g},{frame['center_of_mass_m'][1]:.12g},{frame['center_of_mass_m'][2]:.12g}}};
  constant Real frameInertia[3,3] = [{';'.join(','.join(f'{value:.12g}' for value in row) for row in frame['inertia_com_kg_m2'])}];
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
