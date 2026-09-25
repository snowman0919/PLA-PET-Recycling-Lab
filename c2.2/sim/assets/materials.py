"""VP1 material choices and bounded mass properties for STEP-derived solids.

These are design-screening assumptions, NOT certified grades, measured masses,
structural ratings, or procurement choices. CAD contains single homogeneous solids
for some mixed/purchased items; proxies explicitly keep that uncertainty visible.
"""
from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = "c2.2/sim/assets/materials.py"

# Material density kg/m3, process and temperature bounds are candidate values.
# Printed effective fraction applies to the modeled CAD material volume; voids
# already cut in CAD must not be deducted twice. No strength claim follows.
MATERIALS = {
    "PC_SHEET": dict(density=1200., process="unfilled PC sheet candidate cut/formed; separate metal strike unmodeled", temperature="PC only with measured cold-zone temperature and independent metal safety retention; grade, forming, impact qualification HOLD"),
    "PC_FDM": dict(density=1200., fraction=1.0, bounds=(1020., 1320.), bounds_basis="0.85..1.10 x nominal PC solid-shell mass per CAD volume: print voids and dimensional/warpage sensitivity, NOT bulk PC density range", process="unfilled PC FDM candidate, segmented nominal ~3 mm shell; panel outer face supported on build plate, 6 perimeters at ~0.42 mm line width plus solid gap fill, 100% nominal modeled wall volume (no second infill deduction); panel orientation/seam adhesion unqualified", temperature="dry PC filament, enclosed heated chamber/bed and measured cold-zone exposure assumed; actual grade/warpage/layer impact strength and process validation HOLD"),
    "AL_5052": dict(density=2680., process="sheet/plate Al 5052 candidate; temper and attachment HOLD", temperature="thermal path interface/contact and peak temperature unmeasured"),
    "AL_PROFILE": dict(density=2700., bounds=(1350., 4050.), bounds_basis="0.5..1.5 x nominal Al mass per CAD hollow-box volume: unknown owned T-slot web/slot area, NOT Al alloy density bounds; section second moment remains unmeasured", process="owned Al T-slot extrusion; STEP nominal hollow section is mass proxy, slot/web dimensions must be measured", temperature="profile alloy/temper and joint stiffness unknown"),
    "STEEL": dict(density=7850., process="machined/formed/welded steel candidate; actual grade, weld and heat treatment per part RFQ", temperature="hot-zone grade and measured temperature HOLD"),
    "TOOL_STEEL": dict(density=7800., process="machined tool steel candidate; heat treatment/grinding and edge qualification HOLD", temperature="wear and fatigue qualification HOLD"),
    "ABS_FDM": dict(density=1040., fraction=0.65, bounds=(520., 884.), bounds_basis="0.50..0.85 x nominal ABS density per CAD drum volume: slicer wall/infill and process sensitivity, not bulk resin range", process="unfilled ABS FDM cold-zone candidate; drum axis normal to build plate, 4 perimeters, 6 top/bottom layers, 50% gyroid infill; assumed effective 65% of CAD volume", temperature="assume part remains below 60 C; chamber/adhesion and creep at tension HOLD"),
    "ELASTOMER_BELT": dict(density=1150., process="commercial polymer tread/belt geometry proxy, not a rigid printed load member", temperature="compound, tension and temperature rating HOLD"),
    "PVC_DUCT": dict(density=1380., process="purchased PVC wiring duct geometry proxy", temperature="grade/flame rating and separation HOLD"),
    "PURCHASED_MOTOR": dict(density=2500., bounds=(800., 5000.), process="motor envelope effective-density proxy; no selected motor MPN or measured mass", temperature="electrical/thermal rating HOLD"),
    "PURCHASED_BEARING": dict(density=4600., bounds=(1800., 7800.), process="bearing envelope proxy; rings/balls/cage/air/seals not a solid steel body", temperature="MPN, clearance, grease and temperature HOLD"),
    "PURCHASED_ELECTRICAL": dict(density=1800., bounds=(400., 5000.), process="unselected electrical enclosure/component effective-density proxy; no BOM mass", temperature="electrical/thermal rating HOLD"),
    "PURCHASED_HEATER": dict(density=2800., bounds=(1000., 6000.), process="heater geometry envelope proxy (ceramic/steel/resistance element), not solid steel", temperature="rated heater attachment and control HOLD"),
    "PURCHASED_FAN": dict(density=1200., bounds=(400., 3000.), process="fan assembly envelope proxy; housing/impeller/motor/air", temperature="manufacturer mass and airflow curve HOLD"),
    "SPOOL_REFERENCE": dict(density=800., bounds=(350., 1400.), process="user spool envelope, empty polymer candidate; not an owned or selected spool", temperature="supplier mass/geometry and tension HOLD"),
    "TPU_METAL_PROXY": dict(density=3200., bounds=(1100., 7850.), process="single CAD solid represents TPU tread and metal hub; split thickness unmodeled", temperature="tread compound/adhesion/grip and working temperature HOLD"),
    "STEEL_PRINTED_GUIDE_PROXY": dict(density=7000., bounds=(3000., 7850.), process="single CAD solid approximates steel rider plus small cold-zone printed ABS guide; allocation/steel insert unmodeled", temperature="guide below 60 C; load-bearing steel and fasteners required"),
}

# C2.1 and VP1 parts not present in the C1 instance inventory. Every other
# name must resolve via design/assembly.json or the VP1 BOM; fail closed.
C21 = {
    "FRONT_INPUT_SUPPORT": "STEEL", "REAR_OUTPUT_SUPPORT": "STEEL",
    "INPUT_BEARING_ENVELOPE_UNRATED": "PURCHASED_BEARING",
    "OUTPUT_BEARING_ENVELOPE_UNRATED": "PURCHASED_BEARING",
    "ECCENTRIC_BEARING_ENVELOPE_UNRATED": "PURCHASED_BEARING",
    "C2_FIXED_SHEAR_SENSOR_BORE": "TOOL_STEEL",
    "C2_VERTICAL_DISCHARGE_SCREEN": "STEEL",
    "INPUT_ECCENTRIC_SHAFT": "STEEL",
    "RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE": "STEEL",
    "OUTPUT_PIN_CARRIER_AND_SHAFT": "STEEL",
}

# Manufacturing decision where the source BOM explicitly offers two options.
DECISIONS = {
    "WIND_SPOOL_DRUM": "ABS_FDM",  # steel tube OR printed polymer in VP1 BOM
    "WIND_TRAVERSE_RIDER": "STEEL_PRINTED_GUIDE_PROXY",
    "PULL_ROLLER_FIXED": "TPU_METAL_PROXY",
    "PULL_ROLLER_ADJ": "STEEL",  # integral spring carriage; hub/tread split unmodeled
    "S1_BELT": "ELASTOMER_BELT",
    "S1_TRANSFER_BELT": "ELASTOMER_BELT",
    "EL_WIRE_DUCT": "PVC_DUCT",
}

@lru_cache(maxsize=1)
def _source_inventory():
    assembly = json.loads((REPO / "design/assembly.json").read_text())
    instances = {i["name"]: i["part"] for i in assembly["instances"]}
    with (REPO / "c2.1/bom/vp1_bom_delta.csv").open(newline="") as f:
        delta = {r["item_id"]: r["material_or_type"] for r in csv.DictReader(f)}
    return assembly["parts"], instances, delta


def specification(name: str) -> dict:
    parts, instances, delta = _source_inventory()
    if name in DECISIONS:
        key, provenance = DECISIONS[name], "c2.1/bom/vp1_bom_delta.csv; design choice in " + SOURCE
        label = delta[name]
    elif name in C21:
        key, provenance = C21[name], "c2.1/bom/transmission_bom.csv; " + SOURCE
        label = key
    elif name in ("HOPPER_PANEL_L", "HOPPER_PANEL_R"):
        key, provenance, label = "PC_FDM", "c2.1/src/hopper_panels.py split of cad/parts/HOPPER.step; " + SOURCE, "PC segmented printed shell"
    elif name in ("HOPPER_SEAM_FRONT", "HOPPER_SEAM_REAR"):
        key, provenance, label = "STEEL", "c2.1/src/hopper_panels.py seam rail; " + SOURCE, "1.5 mm steel seam rail candidate"
    elif name.startswith(("C2_THERMAL_SADDLE_", "C2_SADDLE_CAP_")):
        key, provenance, label = "AL_5052", "c2.1/bom/system_bom.csv S2-THERMAL; " + SOURCE, "aluminium candidate"
    elif name.startswith("OUTPUT_ROLLER_"):
        key, provenance, label = "PURCHASED_BEARING", "c2.1/bom/transmission_bom.csv S2-OUT-ROLLER; " + SOURCE, "MPN unselected roller envelope"
    elif name.startswith(("FIXED_RING_PIN_", "SUPPORT_TIE_")):
        key, provenance, label = "STEEL", "c2.1/bom/transmission_bom.csv; " + SOURCE, "steel candidate"
    elif name.startswith(("C2_LEFT_WEAR_SHELL", "C2_RIGHT_WEAR_SHELL", "FRONT_FIXED_RING_PLATE", "REAR_FIXED_RING_PLATE")):
        key, provenance, label = "STEEL", "c2.1/bom/transmission_bom.csv; " + SOURCE, "steel candidate"
    else:
        part = instances.get(name)
        if name == "DRV-SP24-B20_002":
            part = "DRV-SP24-B20"
        if name == "KEY-6-16_002":
            part = "KEY-6-16"
        if part is not None:
            label = parts[part]["material"]
            provenance = f"design/assembly.json parts.{part}.material"
        elif name in delta:
            label = delta[name]
            provenance = f"c2.1/bom/vp1_bom_delta.csv item_id={name}"
        else:
            raise ValueError(f"no material source for STEP part {name}")
        if name.startswith("FR-2040-") or name.startswith("FR-2020-"):
            key = "AL_PROFILE"
        elif name == "FR-BASE":
            key = "AL_5052"
        elif name == "HOP-LID_001":
            key = "PC_SHEET"
        elif name.startswith("BR-"):
            key = "PURCHASED_BEARING"
        elif name.startswith(("DRV-M1_", "DRV-M2_", "PULL_MOTOR_REF", "WIND_MOTOR_REF")):
            key = "PURCHASED_MOTOR"
        elif name.startswith("COOL-FAN"):
            key = "PURCHASED_FAN"
        elif name.startswith(("EX-H100", "EX-H60")):
            key = "PURCHASED_HEATER"
        elif name == "SPOOL-ENV_001":
            key = "SPOOL_REFERENCE"
        elif (name.startswith("EL_") and name != "EL_DIN_RAIL") or name == "EL-PSU_001":
            key = "PURCHASED_ELECTRICAL"
        elif name.startswith("PULL-ROLLER"):
            key = "TPU_METAL_PROXY"
        elif "pc" in label.lower():
            raise ValueError(f"PC composite needs exact part mapping: {name}")
        elif "tool steel" in label.lower():
            key = "TOOL_STEEL"
        elif "steel" in label.lower() or "sheet metal" in label.lower() or any(s in label.lower() for s in ("c45", "scm440", "s45c", "s355")):
            key = "STEEL"
        elif "al " in label.lower() or "aluminium" in label.lower():
            key = "AL_5052"
        elif "polymer belt" in label.lower():
            key = "ELASTOMER_BELT"
        elif "pvc" in label.lower():
            key = "PVC_DUCT"
        else:
            raise ValueError(f"unsupported material for STEP part {name}: {label}")
    spec = MATERIALS[key]
    density = spec["density"] * spec.get("fraction", 1.0)
    lo, hi = spec.get("bounds", (density, density))
    return {
        "material": key, "source_material_label": label,
        "manufacturing_process": spec["process"], "thermal_condition": spec["temperature"],
        "material_source": provenance, "model_source": SOURCE,
        "nominal_density_kg_m3": spec["density"],
        "effective_fraction": spec.get("fraction", 1.0),
        "effective_density_kg_m3": density,
        "effective_density_bounds_kg_m3": [lo, hi],
        "bounds_basis": spec.get("bounds_basis", "effective-density range over simplified purchased/mixed CAD boundary, not measured material density" if lo != hi else "single nominal design assumption; actual grade and geometry unmeasured"),
        "mass_material_status": ("BOUNDED_PROXY_UNRATED" if lo != hi
                                 else "DESIGN_ASSUMPTION_UNRATED"),
    }


def mass_properties(name: str, volume_mm3: float, bbox_mm) -> dict:
    """O(1) BRep-volume mass and bbox-diagonal estimate, not a CAD inertia.

    Upper bounds hold for arbitrary matter inside the given solid bbox about
    the assumed bbox-center COM. Actual COM and off-diagonal tensor are not
    determined; diagonal box values are estimates, not rigorous lower bounds.
    """
    if volume_mm3 <= 0 or len(bbox_mm) != 6:
        raise ValueError(f"{name}: nonpositive volume or invalid bbox")
    b = [float(v) for v in bbox_mm]
    d = [b[i + 3] - b[i] for i in range(3)]
    if min(d) <= 0:
        raise ValueError(f"{name}: degenerate bbox")
    spec = specification(name)
    mass = volume_mm3 * spec["effective_density_kg_m3"] * 1e-9
    mass_bounds = [volume_mm3 * rho * 1e-9 for rho in spec["effective_density_bounds_kg_m3"]]
    inertia = [mass * (d[j] ** 2 + d[k] ** 2) / 12.0
               for j, k in ((1, 2), (0, 2), (0, 1))]
    upper = [mass_bounds[1] * (d[j] ** 2 + d[k] ** 2) / 4.0
             for j, k in ((1, 2), (0, 2), (0, 1))]
    return {
        **spec, "volume_mm3": volume_mm3, "solid_bbox_mm": b,
        "mass_kg": mass, "mass_bounds_kg": mass_bounds,
        "center_of_mass_mm": [(b[i] + b[i + 3]) / 2.0 for i in range(3)],
        "inertia_kg_mm2": inertia,
        "inertia_upper_bound_kg_mm2": upper,
        "inertia_basis": "bbox-center assumed COM; uniform box diagonal estimate at BRep-volume mass; true COM/tensor unmeasured, per-axis upper bound for any mass within bbox (at bbox center)",
        "mass_source": "imported STEP solid BRep volume x effective material density; no per-solid BRep inertia extraction",
    }


MATERIAL_SCOPE = {
    "feedstock_vs_construction": "PLA/PET/TPU are input waste feedstocks, not permission to print load-bearing machine parts; TPU tread is a separate commercial elastomer boundary.",
    "selected": "HOPPER_PANEL_L/R nominal ~3 mm FDM PC shell segments; HOPPER_SEAM_FRONT/REAR 1.5 mm steel upper-wall rails are NOT a full steel lower liner or qualified containment. HOP-LID_001 PC cut sheet has a separate unmodeled metal strike. FEED-BUF_001 and split FEED-BUF-SADDLE/CLAMP are S355 steel design candidates; weld, bolts, cold barrel fit, thermal interface and flow remain HOLD. ABS FDM cold WIND_SPOOL_DRUM plus small traverse eyelet candidate; load paths/shafts/guards in steel, owned profiles in aluminium.",
    "excluded": "PLA (Tg about 55-65 C) excluded from hot zone, load path and permanent guards due to creep/softening; ABS (Tg about 100-110 C) excluded from heater/barrel, cutter/load path, guards and feed throat due to creep, anisotropy and unknown peak temperatures; PC (Tg about 145-150 C) excluded from heater/barrel and high-impact structural interfaces pending measured temperatures, grade and process qualification. No printed keys or bearing seats.",
    "printed_limits": "PC panels assume dry filament, heated enclosed printer, face-supported orientation, six walls and 100% effective CAD wall density; ~3 mm CAD wall already excludes hollow volume, so no second infill factor. Bed fit is bounded by the split design, not proof of printability, seam sealing, layer adhesion or impact containment. ABS drum assumes dry filament, enclosed printer, drum axis normal to build plate, four walls, six skins, 50% infill and effective 65% density; actual slicer mass, residual stress and warm creep must be checked. ABS printed eyelet/guide on WIND_TRAVERSE_RIDER is not separable in the fused STEP; its contribution is folded into a bounded steel/polymer proxy, not double-counted.",
    "boundary": "All densities/grades and effective fill factors are screening choices; mass is not a weighed value. Profile mass uses 0.5..1.5 x nominal CAD hollow-box volume because owned T-slot metal area is unmeasured; this is NOT a material-density bound or a section-I measurement. PC-panel printed mass uses 0.85..1.10 x nominal CAD-wall mass, ABS drum 0.50..0.85 x resin-density CAD volume; slicer/print mass is unmeasured. Purchase boundaries and mixed parts use explicit ranges; static structure mass is inventory only, not a PhysX rigid body. No strength, safety or fabrication release.",
}
