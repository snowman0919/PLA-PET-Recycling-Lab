#!/usr/bin/env python3
"""v0.8 critical interface의 worst-case tolerance stack 단일 생성원."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = "final-design-fabrication-closure-v0.8"
JSON_OUT = ROOT / "calculations/tolerance_stack_final.json"
CSV_OUT = ROOT / "exports/final/interface_catalog.csv"
DOC_OUT = ROOT / "docs/tolerance_and_fit_guide_ko.md"
MIRROR_OUT = ROOT / "exports/fabrication/interface_catalog.csv"
LEGACY_COMMIT = "f3b1e666c95e5f563c834eea6a080f4ab3f689a1"


@lru_cache(maxsize=None)
def source_text(path: str, commit: str = "") -> str:
    if commit:
        return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT, text=True)
    return (ROOT / path).read_text(encoding="utf-8")


def evidence(path: str, needle: str, commit: str = "") -> dict:
    """Pin inspected content and its version, not merely a mutable filename."""
    text = source_text(path, commit)
    hits = [(n, line) for n, line in enumerate(text.splitlines(), 1) if needle in line]
    if len(hits) != 1:
        raise ValueError(f"source selector must be unique: {path}: {needle!r} ({len(hits)})")
    number, excerpt = hits[0]
    return {"path": path, "commit": commit, "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "line": number, "excerpt": excerpt}


def note(part: str) -> dict:
    if part.startswith("CUT-"):
        return evidence(f"exports/cnc/{part}/drawing_notes.md", "중요공차/검사:")
    if part.startswith("DRV-") and part != "DRV-GD-01":
        family = "drive_interface"
    elif part.startswith("TH-"):
        family = "thermal"
    elif part in {"EX-SCR-01", "EX-BAR-01", "EX-DIE-01"}:
        family = "cnc/extruder"
    else:
        family = "fabrication"
    return evidence(f"exports/{family}/parts/{part}/drawing_notes.md", "controlling requirements:")


def printed(part: str) -> dict:
    return evidence("cad/freecad/compact/geometry.py", f'dict(id="{part}", name=')


def numeric_status(limits, required_minimum, required_maximum):
    low, high = limits
    if any(value is not None and not math.isfinite(value) for value in (*limits, required_minimum, required_maximum)):
        return "FAIL"
    if low is None or high is None:
        if required_maximum is None and low is not None and required_minimum is not None:
            return "PASS" if low + 1e-9 >= required_minimum else "FAIL"
        return "NOT_EVALUATED"
    if low > high:
        return "FAIL"
    if required_minimum is None and required_maximum is None:
        return "NOT_EVALUATED"
    return "PASS" if ((required_minimum is None or low + 1e-9 >= required_minimum)
                      and (required_maximum is None or high - 1e-9 <= required_maximum)) else "FAIL"


def assessed(row, limits, required, refs, *, reason="", calculation=None, migration="current-source review", kind="DERIVED_LIMITS"):
    row = dict(row)
    row.update(minimum=None if limits[0] is None else round(limits[0], 6),
               maximum=None if limits[1] is None else round(limits[1], 6),
               required_minimum=required[0], required_maximum=required[1],
               assessment_kind=kind, blockers=reason, migration_note=migration,
               source_refs=json.dumps(refs, ensure_ascii=False, sort_keys=True),
               physical_validation_state="NOT_RUN")
    if calculation is not None:
        row["calculation"] = calculation
    row["numeric_status"] = numeric_status([row["minimum"], row["maximum"]], *required)
    row["status"] = "HOLD" if reason or row["numeric_status"] == "NOT_EVALUATED" else row["numeric_status"]
    return row


def symmetric(nominal: float, *contributors: float) -> list[float]:
    total = sum(abs(value) for value in contributors)
    return [nominal - total, nominal + total]


def clearance(inner: tuple[float, float], outer: tuple[float, float], divisor: float = 1) -> list[float]:
    return [(inner[0] - outer[1]) / divisor, (inner[1] - outer[0]) / divisor]


def interface(interface_id: str, part_a: str, part_b: str, nominal: str, limits: list[float], unit: str,
              components: list[str], calculation: str, criterion: str, required_minimum: float,
              fit: str, finish: str, assembly: str, inspection: str, adjustment: str, thermal: str) -> dict:
    low, high = (round(value, 4) for value in limits)
    return {
        "interface_id": interface_id, "part_a": part_a, "part_b": part_b,
        "nominal_dimension": nominal, "minimum": low, "maximum": high, "unit": unit,
        "components": "; ".join(components), "calculation": calculation,
        "criterion": criterion, "required_minimum": required_minimum,
        "fit_tolerance": fit, "surface_finish": finish, "assembly_method": assembly,
        "inspection_method": inspection, "adjustment_shim_method": adjustment,
        "thermal_condition": thermal, "revision": REV,
        # Only assessed() may release a row after source and both-limit checks.
        "status": "HOLD",
    }


def rows() -> list[dict]:
    screw = clearance((16.20, 16.22), (15.90, 15.92), 2)
    heater_closure_margin = [1.00 - math.pi * (34.20 - 33.97), None]
    feeder = clearance((25.00, 25.05), (24.55, 24.60), 2)
    ligament = [16.985 - 8.11 - 5.45, 17.00 - 8.10 - 5.35]
    thermal_margin = [1.30 - 1.1662, 1.50 - 1.1662]
    alpha = 12e-6
    hot_screw = [
        (16.20 * (1 + alpha * (245 - 20)) - 15.92 * (1 + alpha * (270 - 20))) / 2,
        (16.22 * (1 + alpha * (270 - 20)) - 15.90 * (1 + alpha * (245 - 20))) / 2,
    ]
    data = [
        interface("TS-01", "CUT-01 discs", "CUT-02 spacers/collars", "0.375 selected axial gap", symmetric(.375, .125), "mm", ["selected metal shim/gap 0.375 ±0.125"], "0.375 ± 0.125", "working gap 0.25–0.50", .25, "metal shim controlled", "disc faces Ra≤1.6", "dry stack then collar clamp", "four-position feeler gauge", "0.05/0.10/0.25 mm metal shim only", "20–40 °C dry assembly"),
        interface("TS-02", "CUT-05 shafts", "CUT-03 matched plates", "0.125 axial float", symmetric(.125, .075), "mm", ["collar/bearing datum allowance ±0.05", "selected shim allowance ±0.025"], "0.125 ± (0.050 + 0.025)", "axial float ≥0.05", .05, "one fixed/one floating bearing per shaft", "journal Ra≤0.8", "metal collars retain inner rings", "dial indicator", "select metal shim", "20–80 °C"),
        interface("TS-03", "DRV-03/DRV-03R phase gears", "CUT-03 bearing centres", "48.00 centre / released pair", [0, .35], "mm", ["released BRep cold pair", "loaded shaft/plate CalculiX bound"], "cold BRep backlash ± loaded centre movement", "loaded backlash >0 and combined phase error ≤1°", 0, "assembled cold backlash 0.120–0.140 over full rotation", "gear flank Ra≤3.2", "key+dowel then bolt", "indicator over one full mesh rotation + optical phase", "reject/remake if acceptance is missed", "20±2 °C receipt; loaded digital screen"),
        interface("TS-04", "CUT-03 front plate", "CUT-03 rear plate", "seat-axis parallelism", [0, .05], "mm/140mm", ["matched pair functional limit 0.05/140"], "match-machine both plates and inspect the resulting pair", "parallelism ≤0.05/140", 0, "match-machine as one identified pair", "seat Ra≤1.6", "temporary datum bars before frame torque", "two ground bars + indicator", "reject/remake matched pair; frame shims do not repair seat error", "20±2 °C inspection"),
        interface("TS-05", "EX-SCR-01 flight", "EX-BAR-01 bore", "radial cold clearance", screw, "mm", ["bore ID 16.20 +0.02/0", "flight OD 15.92 -0.02/0"], "(ID limit − OD opposite limit) / 2", "radial clearance ≥0.14", .14, "matched supplier pair", "flight/bore Ra≤0.8", "matched supplier pair", "micrometer + 3-point bore gauge at three stations", "reject or finish-hone; no printed shim", "20 °C cold"),
        interface("TS-06", "EX-BAR-01 bore axis", "EX-DIE-01 channel axis", "axis offset", [0, .025 + .025], "mm", ["barrel datum-axis location ±0.025", "die channel-axis location ±0.025"], "|barrel| + |die| = 0.050 max", "axis offset ≤0.05", 0, "dowel/datum controlled", "gasket face Ra≤1.6", "dowel/bolt on copper gasket", "coaxial pin + indicator", "0.05 mm copper face shim", "20 °C assembly / 270 °C check"),
        interface("TS-07", "TH-BH-01 heater free-state ID", "EX-BAR-01 OD", "usable split-closure reserve", [heater_closure_margin[0], heater_closure_margin[0]], "mm", ["TH-BH-01 free-state ID34.10–34.20", "EX-BAR-01 OD33.97–34.00", "usable split-closure travel≥1.00"], "1.00 − π(34.20−33.97)", "closure reserve ≥0.25", .25, "custom split clamp; closure travel≥1.00", "barrel Ra≤1.6", "close clamp evenly to sector-contact acceptance", "0.05 mm feeler penetration≤5 mm at 8 sectors excluding split±10°", "supplier clamp only; reject if closure/contact misses", "20 °C install / 300 °C design"),
        interface("TS-08", "TEMP-01..03 bore tip", "EX-BAR-01 melt bore", "remaining ligament", ligament, "mm", ["barrel OD radius 16.985–17.000", "melt-bore radius 8.100–8.110", "probe-bore depth 5.35–5.45"], "OD radius − melt radius − blind depth", "ligament ≥3.32", 3.32, "Ø3.20 +0.05/0 flat-bottom blind 5.40 ±0.05", "bore Ra≤3.2", "depth-stop flat-bottom bore", "ultrasonic wall or depth+OD/ID", "reject part; no repair shim", "20 °C inspect / 270 °C analysis"),
        interface("TS-09", "FD-MET-02 auger", "FD-MET-01 housing", "radial running clearance", feeder, "mm", ["housing ID 25.00 +0.05/0", "auger OD 24.60 -0.05/0"], "(housing ID limit − auger OD opposite limit) / 2", "radial clearance ≥0.20", .20, "running fit", "Ra≤3.2 deburred", "Ø8 common auger/agitator shaft with removable coupling", "bore gauge + micrometer", "finish-turn auger OD", "20–80 °C"),
        interface("TS-10", "FM-RL-01 roller pair", "FM-EB-01 eccentric pair", "1.80 nominal unloaded gap", [1.60, 1.90], "mm", ["outer-seat centres40.80", "eccentric offset1.00±0.02", "full-rotation functional acceptance"], "adjust paired eccentric bushes equally, then measure the complete rotation", "unloaded gap 1.60–1.90 over full rotation", 1.60, "Ø16 H7/g6 eccentric bush; paired index≤0.5°", "roller TIR≤0.05", "set both metal bushes under lockout; clamp M3", "feeler sweep over one full rotation", "continuous ±30° eccentric adjustment; no printed shim", "20±2 °C"),
        interface("TS-11", "PPR-C06 X gauge", "PPR-C06 Y gauge", "optical centreline offset", [0, .05 + .05], "mm", ["X fixture centre ±0.05", "Y fixture centre ±0.05"], "|X| + |Y| = 0.10 max", "offset ≤0.10", 0, "fixture aligned", "matte optical bridge", "dowel then fasten", "calibration wire scan", "metal gauge shim", "ambient stable"),
        interface("TS-12", "SP-TR-01 matched end-plate pair", "installed Ø8 rods", "assembled rod parallelism", [0, .10], "mm/160mm", ["matched-pair functional limit 0.10/160"], "match-machine the end plates, install the selected rods, then inspect the complete 160 mm span", "parallelism ≤0.10/160", 0, "matched end plates; complete-assembly acceptance", "rod Ra≤0.8", "loose fit, indicator sweep, then torque", "indicator full 160 mm span", "reject/remake matched pair or rods; no printed shim", "20±2 °C inspection"),
        interface("TS-13", "guards/panels", "moving envelopes", "3.0 static clearance", symmetric(3, .5, .5), "mm", ["nominal CAD gap 3.0", "panel position ±0.5", "motion envelope ±0.5"], "3.0 ± (0.5 + 0.5)", "moving clearance ≥2.0", 2, "metal guard spacers", "deburr R0.3", "fasten after motion sweep", "feeler + envelope CAD", "metal washer/spacer", "cold motion"),
        interface("TS-14", "hot shield", "300 °C hot envelope", "12.0 static clearance", symmetric(12, 1, 1), "mm", ["nominal CAD gap 12.0", "shield position ±1.0", "hot envelope allowance ±1.0"], "12.0 ± (1.0 + 1.0)", "hot clearance ≥10.0", 10, "grounded metal shield", "deburr R0.3", "fasten after thermal-envelope check", "feeler + envelope CAD", "metal washer/spacer", "20→300 °C"),
        interface("TS-15", "ExtruderFrontSlidingGuide (EX-MT-02)", "EX-BAR-01", "remaining axial thermal margin", thermal_margin, "mm", ["available cold travel 1.30–1.50", "predicted 25→270 °C growth 1.1662"], "available travel limit − predicted growth", "remaining travel ≥0", 0, "rear datum fixed; front guide axial sliding", "guide Ra≤1.6 dry-film compatible", "cold datum then verify free slide", "depth gauge before/after heat simulation", "metal stop/shim", "25→270 °C"),
        interface("TS-16", "EX-SCR-01 flight", "EX-BAR-01 bore", "radial hot differential clearance", hot_screw, "mm", ["SCM440 alpha 12e-6/K", "worst bore 245 °C / screw 270 °C", "opposite bound bore 270 °C / screw 245 °C"], "(hot bore ID − hot screw OD) / 2", "hot radial clearance ≥0.13", .13, "matched nitrided SCM440 pair", "flight/bore Ra≤0.8", "cold clearance report then free thermal growth", "temperature map + three-station bore/flight report", "reject or finish-hone; no shim", "20→270 °C differential bound"),
    ]
    data = review_stacks(data)
    return data + mating_rows(data)


def review_stacks(data):
    """Separate actual calculations from historical acceptance windows/proposals."""
    refs = {
        "TS-01": [note("CUT-01"), note("CUT-02"), evidence("cad/freecad/compact/geometry.py", "axial_offset = 0.0 if cx == 105 else 6.5")],
        "TS-02": [note("CUT-05"), note("CUT-03"), note("CUT-08")],
        "TS-03": [note("CUT-03"), note("DRV-03"), note("DRV-03R"),
                  evidence("analysis/final_validation/results/v0.8/phase_pair_backlash_candidate.json", '"cad_pair_backlash_bound_mm": ['),
                  evidence("analysis/final_validation/results/v0.8/loaded_phase.json", '"refinement": 16,')],
        "TS-04": [note("CUT-03")], "TS-05": [note("EX-BAR-01"), note("EX-SCR-01")],
        "TS-06": [note("EX-BAR-01"), note("EX-DIE-01")],
        "TS-07": [note("TH-BH-01"), note("EX-BAR-01")],
        "TS-08": [note("EX-BAR-01"), evidence("cad/generation/generate_manufacturing.py", "- T1/T2/T3 radial blind sensor bores는")],
        "TS-09": [note("FD-MET-01"), note("FD-MET-02")],
        "TS-10": [note("FM-RL-01"), note("FM-PL-01"), note("FM-EB-01")],
        "TS-11": [printed("PPR-C06")], "TS-12": [note("SP-TR-01")],
        "TS-13": [note("DRV-GD-01"), printed("PPR-C07"), evidence("validation/results/full_motion.json", '"guard_to_moving_clearance_mm"')],
        "TS-14": [note("EX-SH-01"), printed("PPR-C05"), evidence("validation/results/full_motion.json", '"hot_shield_to_abs_duct_clearance_mm"')],
        "TS-15": [evidence("exports/final/manufacturing/RFQ/manifest.csv", f"ExtruderFrontSlidingGuide,{REV},"),
                  evidence("analysis/final_validation/results/v0.8/hot_zone_digital_qualification.json", '"minimum_full_length_travel_margin_mm"')],
        "TS-16": [note("EX-BAR-01"), note("EX-SCR-01"),
                  evidence("analysis/final_validation/results/v0.8/hot_zone_digital_qualification.json", '"minimum_radial_clearance_mm"')],
    }
    # None signifies an unavailable bound, not zero or a guessed donor fit.
    unknown = {
    }
    upper = {"TS-01": .50, "TS-02": .20, "TS-03": .35, "TS-04": .05,
             "TS-05": .16, "TS-06": .05, "TS-09": .25, "TS-10": 1.90, "TS-11": .10, "TS-12": .10}
    result = []
    for original in data:
        r = dict(original); iid = r["interface_id"]
        historical = evidence("calculations/tolerance_stack_final.json", f'"interface_id": "{iid}"', LEGACY_COMMIT)
        limits = [r["minimum"], r["maximum"]]
        reason = unknown.get(iid, "")
        required = (r["required_minimum"], upper.get(iid))
        calc = r["calculation"]; kind = "DERIVED_LIMITS"
        if reason:
            limits = [None, None]; calc = "NOT_EVALUATED — component tolerance allocation absent"
            r["components"] = "source nominal/assembly criterion only; no qualified component intervals"
            r["assembly_method"] = "use cited source datums under lockout; pending qualified assembly stack"
            r["adjustment_shim_method"] = "HOLD — adjustment must be dimensioned; no improvised rework"
        if iid == "TS-01":
            limits = [.25, .50]; kind = "COMPLETE_ASSEMBLY_FUNCTIONAL_ACCEPTANCE"
            r["nominal_dimension"] = "numbered CUT-01/CUT-02 two-shaft matched stack; CAD stagger6.5"
            r["components"] = "10 position-engraved match-ground spacers plus 0.05/0.10/0.25 mm metal shims; all 11 opposing gaps"
            calc = "match-grind/lap the numbered spacer set, shim with metal only, then accept every gap over one full hand rotation"
            r["assembly_method"] = "assemble the identified two-shaft set under lockout; do not interchange spacers"
            r["inspection_method"] = "feeler sweep of all 11 gaps over one full hand rotation; record shaft/position map"
            r["adjustment_shim_method"] = "0.05/0.10/0.25 mm ground metal shim only; reject/remake if any gap misses"
            reason = ""
        elif iid == "TS-02":
            limits = [.05, .20]; required = (.05, .20)
            r["components"] = "identified front fixed/rear floating CUT-10 rings; 0.05/0.10/0.20 mm ground metal shims; both complete shafts"
            calc = "shim rear outer-ring retention, then accept each shaft directly by dial indicator over one full hand rotation"
            r["assembly_method"] = "clamp front bearing; leave rear outer ring floating; install engraved CUT-10 rings and ground metal shims under lockout"
            r["inspection_method"] = "dial-indicator axial sweep on each complete shaft over one full hand rotation"
            r["adjustment_shim_method"] = "0.05/0.10/0.20 mm ground metal shim only; reject/remake if either shaft misses"
            reason = ""
            kind = "COMPLETE_ASSEMBLY_FUNCTIONAL_ACCEPTANCE"
        elif iid == "TS-03":
            cold = json.loads(source_text("analysis/final_validation/results/v0.8/phase_pair_backlash_candidate.json"))
            loaded = json.loads(source_text("analysis/final_validation/results/v0.8/loaded_phase.json"))
            limits = loaded["meshes"][-1]["backlash_range_mm"]
            required = (0, .35)
            angle = loaded["meshes"][-1]["backlash_angular_bound_deg"]
            checks = loaded.get("checks", {})
            qualified = (cold.get("cad_pair_backlash_bound_mm") == [0.1256637061435917, 0.13404128655316452]
                         and loaded.get("status") == "PASS" and all(checks.values()) and angle <= 1)
            reason = "" if qualified else "Released cold-pair or loaded-phase evidence is not qualified/current."
            r["components"] = "cold BRep 0.125664–0.134041; loaded refinement16 centre movement0.034320"
            calc = "released cold BRep pair ± CalculiX shaft/plate movement = 0.100681–0.159024; loaded backlash angle0.379642°; combined path0.903639°"
            kind = "RELEASED_BREP_AND_LOADED_FEA"
        elif iid == "TS-06":
            limits = [0, .024]; required = (0, .05)
            r["components"] = "barrel/die dowel-hole true position Ø0.02 each; Ø3 H7=3.000-3.010; selected dowel Ø3 m6=3.002-3.008; maximum radial play0.004"
            calc = "0.010 barrel axis error +0.010 die axis error +0.004 maximum radial dowel play =0.024 mm"
            r["fit_tolerance"] = "2x Ø3 H7 holes / selected Ø3 m6 dowels; true position Ø0.02 to each melt axis"
            r["assembly_method"] = "press selected dowels into barrel; locate die and clearance gasket on both dowels; M4 bolts provide clamp only"
            r["inspection_method"] = "CMM hole true-position reports plus coaxial pin/indicator check before gasketed assembly"
            r["adjustment_shim_method"] = "reject/remake locating holes; copper face gasket is axial seal only"
            reason = ""
            kind = "GD_AND_ISO286_WORST_CASE"
        elif iid == "TS-07":
            limits = [1.00 - math.pi * (34.20 - 33.97), None]; required = (.25, None)
            calc = "minimum closure reserve=1.00−π(34.20−33.97)=0.277434 mm"
            r["criterion"] = "usable closure reserve≥0.25 mm; physical 8-sector contact inspection remains NOT_RUN"
            reason = ""
            kind = "FREE_STATE_ID_AND_CLAMP_TRAVEL_WORST_CASE"
        elif iid == "TS-08":
            required = (3.32, None); r["criterion"] = "released minimum ligament≥3.32"
            r["assembly_method"] = "machine specified flat-bottom geometry; no generic drill-cone substitution; probe insertion remains controlled separately by IF-025"
            # The manufacturing source explicitly releases flat-bottom depth5.40±0.05.
            current = source_text("cad/generation/generate_manufacturing.py")
            if "depth5.40 ±0.05" not in current:
                limits = [None, None]; reason = "Blind-depth interval not released by manufacturing source."
            else:
                # Conservative tip-plane bound: ignoring the beneficial cos(theta)
                # depth reduction, subtract the full permitted axis offset as well.
                tip_projection = 1.625 * math.sin(math.atan(.10 / 5.5))
                limits = [16.985 - 8.11 - 5.45 - .05 - tip_projection, None]
                r["components"] = "OD33.97–34.00 / ID16.20–16.22 / flat-bottom depth5.35–5.45; axis offset bounded0.05; sensor radius≤1.625 and tilt atan(0.10/5.5)"
                calc = "16.985−8.110−5.450−0.050−1.625*sin(atan(0.10/5.5)); conservative flat-tip screen"
                reason = "" if limits[0] >= 3.32 else "Released sensor-bore geometry does not preserve3.32 mm minimum ligament."
                kind = "TILTED_ECCENTRIC_TIP_SCREEN"
        elif iid == "TS-11":
            limits = [0, .10]; required = (0, .10)
            r["components"] = "one straight Ø1.75 calibration wire; X/Y optical pair; match-drilled mounting datum; complete-pair scan"
            calc = "align both optical centres to one calibration wire, match-drill, fasten, then directly accept measured X/Y offset"
            r["assembly_method"] = "fixture both gauges on one straight calibration wire; match-drill mounting datum; fasten at0.5 N.m"
            r["inspection_method"] = "calibration-wire scan of both axes; measured centreline offset≤0.10"
            r["adjustment_shim_method"] = "repeat match-drill alignment before final fastening; reject/remake if scan misses0.10"
            reason = ""
            kind = "COMPLETE_ASSEMBLY_FUNCTIONAL_ACCEPTANCE"
        elif iid == "TS-13":
            motion = json.loads(source_text("validation/results/full_motion.json"))
            nominal = min(motion.get("guard_to_moving_clearance_mm", {}).values(), default=0)
            limits = [nominal - 1, nominal + 1]
            reason = "" if motion.get("status") == "PASS" and limits[0] >= 2 else "Current B-Rep guard clearance and ±0.5 mm position allowances do not preserve the 2 mm minimum."
            r["nominal_dimension"] = f"{nominal:.3f} minimum released B-Rep clearance"
            r["components"] = f"FreeCAD B-Rep minimum nominal{nominal:.3f}; guard position±0.5; moving-axis position±0.5"
            calc = f"{nominal:.3f} ± (0.5 + 0.5) = {limits[0]:.3f}–{limits[1]:.3f}"
            kind = "RELEASED_BREP_AND_POSITION_ALLOWANCE"
        elif iid == "TS-14":
            motion = json.loads(source_text("validation/results/full_motion.json"))
            nominal = min(motion.get("hot_shield_to_abs_duct_clearance_mm", {}).values(), default=0)
            limits = [nominal - 2, nominal + 2]
            reason = "" if motion.get("status") == "PASS" and limits[0] >= 10 else "Current B-Rep clearance and ±1 mm face allowances do not preserve the 10 mm minimum."
            r["components"] = f"FreeCAD B-Rep minimum nominal{nominal:.3f}; shield position±1; duct position±1"
            calc = f"{nominal:.3f} ± (1.0 + 1.0) = {limits[0]:.3f}–{limits[1]:.3f}"
            kind = "RELEASED_BREP_AND_POSITION_ALLOWANCE"
        elif iid == "TS-15":
            hotq = json.loads(source_text("analysis/final_validation/results/v0.8/hot_zone_digital_qualification.json"))
            margin = hotq.get("thermal_fit", {}).get("minimum_full_length_travel_margin_mm")
            travel = hotq.get("thermal_fit", {}).get("declared_cold_axial_travel_mm")
            qualified = hotq.get("status") == "PASS" and isinstance(margin, (int,float)) and margin >= .15 and travel >= 1.50
            limits = [margin, None] if qualified else [None, None]; r["part_a"] = "ExtruderFrontSlidingGuide"
            r["components"] = f"cold axial travel {travel} mm; 300 C / alpha upper-bound full-length remaining margin {margin} mm"
            calc = "current hot-zone qualification: declared cold travel minus worst 300 C full-length free growth"
            reason = "" if qualified else "Current hot-zone digital qualification does not preserve >=0.15 mm axial margin."
            kind = "CURRENT_HOT_ZONE_DIGITAL_ENVELOPE"
        elif iid == "TS-16":
            hotq = json.loads(source_text("analysis/final_validation/results/v0.8/hot_zone_digital_qualification.json"))
            hot = hotq.get("screw_barrel_hot_clearance", {})
            minimum = hot.get("minimum_radial_clearance_mm")
            qualified = hotq.get("status") == "PASS" and isinstance(minimum, (int,float)) and minimum >= .13
            limits = [minimum, max((r.get("radial_clearance_mm",minimum) for r in hot.get("cases",[])), default=minimum)] if qualified else [None,None]
            r["components"] = "alpha 12/12.3/17e-6/K sensitivity; bore/screw 245/270 C and 270/245 C directions"
            calc = "minimum radial clearance over all current hot-zone differential-expansion sensitivity cases"
            reason = "" if qualified else "Current hot-zone digital qualification does not preserve >=0.13 mm radial clearance."
            kind = "CURRENT_HOT_ZONE_DIGITAL_ENVELOPE"
        r = assessed(r, limits, required, [historical, *refs[iid]], reason=reason, calculation=calc, kind=kind)
        if iid in {"TS-02", "TS-05", "TS-09", "TS-10", "TS-12"}:
            r["criterion"] = f"{required[0]} ≤ {r['nominal_dimension']} ≤ {required[1]} {r['unit']}"
        result.append(r)
    return result


def mating_rows(stacks):
    legacy_path = "exports/fabrication/interface_catalog.csv"
    legacy = list(csv.DictReader(io.StringIO(source_text(legacy_path, LEGACY_COMMIT))))
    # Exact old ID -> actual current parts, dimensions, sources, unresolved issue.
    specs = {
        "IF-001": ("CUT-05/CUT-05R", "SKF 61905-2RS1", "shaft24.987-25.000 / bearing bore24.990-25.000", [note("CUT-05"), evidence("docs/final/61905_interface_basis_ko.md", "보어 평균직경")], ""),
        "IF-002": ("SKF 61905-2RS1", "CUT-03", "bearing OD41.989-42.000 / seat42.000-42.025 H7", [note("CUT-03"), evidence("docs/final/61905_interface_basis_ko.md", "외륜 평균직경")], ""),
        "IF-003": ("SKF 61905-2RS1", "CUT-03/CUT-10", "front fixed / rear outer-ring floating; axial float0.05-0.20", [note("CUT-03"), note("CUT-10"), evidence("docs/final/61905_interface_basis_ko.md", "폭 한계")], ""),
        "IF-004": ("CUT-05/CUT-05R", "CUT-01/CUT-02", "shaft24.987-25.000; cutter bore25.010-25.020; spacer bore25.100-25.150", [note("CUT-05"), note("CUT-01"), note("CUT-02")], ""),
        "IF-005": ("CUT-05R", "DRV-02", "shaft24.987-25.000 / hub25.010-25.030; key5.995-6.000 / ways6.005-6.010", [note("CUT-05R"), note("DRV-02")], ""),
        "IF-006": ("DRV-02", "#35 30T sprocket blank", "match-drilled 4×Ø6.6 PCD36.00±0.05; face≥6; assembled tooth-root TIR≤0.10", [note("DRV-02")], ""),
        "IF-007": ("#35 chain", "12T/30T sprockets + DRV-A60", "pitch9.525; 40 pitches; calculated C86.167 within slot range81–99; slack2–3%", [note("DRV-01"), note("DRV-A60")], ""),
        "IF-008": ("TT Motor GMP60-60127-2460 ratio47 reference", "DRV-A60/DRV-F01A", "pilot31.95–32.00/bore32.05–32.10; shaft11.95–12.00/D-bore12.02–12.05; flat10.85–10.90/10.92–10.95", [note("DRV-A60"), note("DRV-F01A"), evidence("docs/final/gmp60_reference_interface_basis_ko.md", "명시된 수령 범위 안의 GMP60 기준 변형에 한해 IF-008")], ""),
        "IF-009": ("DRV-03/DRV-03R", "CUT-05/CUT-05R + selected key", "bore25.010-25.020 / shaft24.987-25.000; key7.995-8.000 / ways8.005-8.010", [note("DRV-03"), note("DRV-03R"), note("CUT-05"), note("CUT-05R")], ""),
        "IF-010": ("FM-GA-01", "SKF 625-2Z", "shaft4.992-5.000 / bearing bore4.992-5.000", [note("FM-GA-01"), evidence("docs/final/625_6001_interface_basis_ko.md", "625 보어 한계")], ""),
        "IF-011": ("SKF 625-2Z", "FM-GR-01/FM-GC-01", "bearingOD15.992-16.000 / seat16.000-16.018 H7; pocket5.10 / width4.880-5.000; cap bore15.00-15.10", [note("FM-GR-01"), note("FM-GC-01"), evidence("docs/final/625_6001_interface_basis_ko.md", "625 보어 한계")], ""),
        "IF-012": ("FM-GA-01", "PPR-C08 ×2", "shaft4.992-5.000 / finished bores5.20-5.40; loose T-slot alignment", [note("FM-GA-01"), printed("PPR-C08")], ""),
        "IF-013": ("FM-RL-01 roller pair", "FM-EB-01/FM-PL-01", "Ø16 H7/g6 eccentric bush; unloaded gap1.60–1.90", [note("FM-RL-01"), note("FM-EB-01"), note("FM-PL-01")], ""),
        "IF-014": ("SP-AX-01", "SP-DA-01/SP-RL-01/SP-DS-01", "shaft7.991-8.000 / bores8.200-8.250; motion±25deg", [note("SP-AX-01"), note("SP-DA-01"), note("SP-RL-01"), note("SP-DS-01")], ""),
        "IF-015": ("2× Ø8 h6 ground steel rods", "PPR-C10/SP-TR-01", "rods7.991-8.000 / carriage8.40-8.50 / end plates8.20-8.30", [printed("PPR-C10"), note("SP-TR-01")], ""),
        "IF-016": ("SP-SH-01", "SKF 6001-2RSH", "shaft11.989-12.000 / bearing bore11.992-12.000", [note("SP-SH-01"), evidence("docs/final/625_6001_interface_basis_ko.md", "6001 보어 한계")], ""),
        "IF-017": ("SKF 6001-2RSH", "SP-BP-01/SP-BR-01", "bearingOD27.991-28.000 / seat28.000-28.021 H7; pocket8.05-8.10 / bearing width7.880-8.000; retainer relief26.00-26.10", [note("SP-BP-01"), note("SP-BR-01"), evidence("docs/final/625_6001_interface_basis_ko.md", "6001 보어 한계")], ""),
        "IF-018": ("PPR-C09", "SP-SH-01/received spool", "finished bore12.20-12.40 / shaft11.989-12.000; M6 through clamp", [printed("PPR-C09"), note("SP-SH-01")], ""),
        "IF-019": ("EX-SCR-01", "EX-BAR-01", "OD15.92 -0.02/0 / ID16.20 +0.02/0", [note("EX-SCR-01"), note("EX-BAR-01")], ""),
        "IF-020": ("EX-SCR-01 thrust seat/shoulder", "NSK 51102/EX-THR-01", "seat14.982-15.000 / shoulder23.00-23.05; bearing15×28×9; pocket28.30-28.35×9.10-9.15", [note("EX-SCR-01"), note("EX-THR-01"), evidence("analysis/final_validation/results/v0.8/extruder_thrust_stack_candidate.json", '"housing_clearance_over_0p25_mm": true')], ""),
        "IF-021": ("FD-MET-02", "FD-MET-01", "OD24.60 -0.05/0 / ID25.00 +0.05/0", [note("FD-MET-02"), note("FD-MET-01")], ""),
        "IF-022": ("FD-MET-03", "FD-MET-02/FD-CP-01/EG17-G10", "shaft7.978-8.000; auger bore8.200-8.300; coupling bores8.050-8.080; matched Ø3.00-3.05 cross-holes", [note("FD-MET-03"), note("FD-MET-02"), note("FD-CP-01"), note("FD-DA-01"), evidence("docs/final/feeder_reference_drive_ko.md", "5/2.2 = 2.273")], ""),
        "IF-023": ("EX-BAR-01", "TH-BH-01 ×3", "barrel33.97–34.00 / free-state heater34.10–34.20 / usable closure≥1.00", [note("EX-BAR-01"), note("TH-BH-01")], ""),
        "IF-024": ("EX-DIE-01", "TH-DIE-01", "boreØ6.55 H7 =6.550–6.565 / Tempco Type CG heater6.487–6.513", [note("EX-DIE-01"), note("TH-DIE-01"), evidence("calculations/run_engineering.py", "hole_min=6.550; hole_max=6.565"), evidence("docs/final/die_heater_selection_basis_ko.md", "Ø6.500 ±0.013 mm")], ""),
        "IF-025": ("EX-BAR-01", "TH-TC-01 at TEMP-01..03", "bore3.20-3.25 flat-bottom depth5.35-5.45 / probe2.97-3.03 / stop5.15-5.25", [note("EX-BAR-01"), note("TH-TC-01"), evidence("docs/final/thermocouple_selection_basis_ko.md", "- sheath `Ø3.00 ±0.03 mm`, 전체 길이 `25.40 ±0.25 mm`")] , ""),
        "IF-026": ("EX-DIE-01", "TH-TC-01 at TEMP-04", "bore3.20-3.25 depth11.95-12.05 / probe2.97-3.03 / stop9.95-10.05", [note("EX-DIE-01"), note("TH-TC-01"), evidence("docs/final/thermocouple_selection_basis_ko.md", "- T1–T3 tip-to-collar `5.20 ±0.05 mm`; T4 tip-to-collar `10.00 ±0.05 mm`")] , ""),
        "IF-027": ("removed hopper-maintenance PTC", "external predry architecture", "no active mating interface", [evidence("docs/final/release_notes_v1.0.0-rc1_ko.md", "REMOVED_FROM_ACTIVE_ARCHITECTURE")], ""),
        "IF-028": ("M3 through-bolts", "PPR-C06/PPR-C11", "M3 major diameter≤3.00 / finished holes3.40-3.50", [printed("PPR-C06"), printed("PPR-C11")], ""),
        "IF-029": ("M4 screw/washer/nyloc", "PPR-C01/PPR-C10", "M4 major diameter≤4.00 / finished through bores4.50–4.70", [printed("PPR-C01"), printed("PPR-C10")], ""),
        "IF-030": ("M3/M4/M5/M6 fasteners and spring pin", "individual printed/metal joints", "30 uniquely identified joint contracts", [printed("PPR-C02"), printed("PPR-C03"), printed("PPR-C04"), note("CUT-03"), evidence("exports/final/bom/fastener_schedule.csv", "joint_id,part_ids,specification,quantity,torque_Nm,locking,tool,inspection,source,verification_state"), evidence("docs/final/assembly_steps.csv", "step_number,part_ids_quantity,required_tools,fasteners,torque,orientation,clearance_tolerance,drawing,inspection_method,pass_fail,next_prerequisite")], ""),
        "IF-031": ("FD-HOP-01/FD-GSK-01", "FD-MET-01 registered flange", "spigot28.77–28.80 / socket28.90–28.93; hopper flow24.90–25.00 / housing25.00–25.05; gasket compressed0.35–0.40", [note("FD-HOP-01"), note("FD-GSK-01"), note("FD-MET-01")], ""),
        "IF-032": ("PPR-C03 ×4", "FD-BIN-01", "sheet1.00±0.05; printed slot1.40±0.30", [printed("PPR-C03"), note("FD-BIN-01")], ""),
    }
    by_stack = {r["interface_id"]: r for r in stacks}
    result = []
    for previous in legacy:
        iid = previous["interface_id"]
        a, b, nominal, refs, reason = specs[iid]
        historical = evidence(legacy_path, f",{iid},", LEGACY_COMMIT)
        base = interface(iid, a, b, nominal, [0, 0], "mm", [nominal], "NOT_EVALUATED — nominal is not a tolerance interval",
                         "resolve both mating limits and acceptance", 0, nominal,
                         "NOT_SPECIFIED — resolve source finish requirement", previous["assembly_method"],
                         previous["inspection_method"], "HOLD — no improvised rework", "20 °C cold; physical NOT_RUN")
        row = assessed(base, [None, None], (None, None), [historical, *refs], reason=reason,
                       migration="historical ID retained; current source dimensions/part IDs replace obsolete values")
        if iid in {"IF-013", "IF-019", "IF-021", "IF-023"}:
            target = {"IF-013": "TS-10", "IF-019": "TS-05", "IF-021": "TS-09", "IF-023": "TS-07"}[iid]
            row = {**by_stack[target], "interface_id": iid, "part_a": a, "part_b": b,
                   "source_refs": json.dumps([historical, *refs], ensure_ascii=False, sort_keys=True),
                   "migration_note": f"compatibility alias for {target}; not extra mating coverage"}
        elif iid == "IF-001":
            row = assessed(row, [-.010, .013], (-.010, .013), [historical, *refs], kind="SKF_NORMAL_AND_H6_LIMITS",
                           calculation="bearing bore opposite limit - shaft opposite limit = -0.010–+0.013 mm")
            row["criterion"] = "diametral transition fit -0.010–+0.013 mm; receipt gauge and press/rotation check required"
        elif iid == "IF-002":
            row = assessed(row, [0, .036], (0, .036), [historical, *refs], kind="SKF_NORMAL_AND_H7_LIMITS",
                           calculation="housing seat opposite limit - bearing OD opposite limit = 0.000–0.036 mm")
            row["criterion"] = "stationary outer-ring H7 fit 0.000–0.036 mm; retainer and receipt inspection required"
        elif iid == "IF-003":
            row = {**by_stack["TS-02"], "interface_id": iid, "part_a": a, "part_b": b,
                   "source_refs": json.dumps([historical, *refs], ensure_ascii=False, sort_keys=True),
                   "migration_note": "bearing outer-ring retention/floating arrangement controlled by TS-02 complete-assembly acceptance"}
        elif iid == "IF-004":
            row = assessed(row, [.010, .163], (0, .170), [historical, *refs], kind="DRAWING_OPPOSITE_LIMITS",
                           calculation="CUT-01 diametral clearance0.010–0.033; CUT-02 clearance0.100–0.163 mm")
            row["criterion"] = "cutter clearance0.010–0.033 and non-torque spacer clearance0.100–0.170 mm"
        elif iid == "IF-005":
            row = assessed(row, [.010, .043], (0, .050), [historical, *refs], kind="DRAWING_OPPOSITE_LIMITS",
                           calculation="hub bore - shaft =0.010–0.043; key side clearance=0.005–0.015 mm")
            row["criterion"] = "diametral clearance0–0.050 and key side clearance0.005–0.015 mm"
        elif iid == "IF-006":
            row = assessed(row, [0, .10], (0, .10), [historical, *refs], kind="MATCH_DRILLED_ASSEMBLY_AND_TIR_ACCEPTANCE",
                           calculation="hub used as drill jig; assembled tooth-root radial TIR measured over one full revolution =0.000–0.100 mm")
            row["criterion"] = "face≥6 mm; 4×Ø6.6 PCD36.00±0.05; assembled tooth-root radial TIR0–0.10 mm"
            row["assembly_method"] = "clamp standard #35 30T blank face to DRV-02, indicate tooth-root circle, match-drill four holes, deburr, torque M6×4 to10 N.m"
            row["inspection_method"] = "verify face and hole pattern; dial-indicate tooth-root circle through one full revolution after torque"
        elif iid == "IF-007":
            row = assessed(row, [86.167, 86.167], (81, 99), [historical, *refs], kind="STANDARD_CHAIN_EQUATION_AND_COMPLETE_ASSEMBLY_ACCEPTANCE",
                           calculation="ANSI two-sprocket equation for p9.525, z12/30, L40 gives C=86.167 mm; 18 mm chain-direction slots about nominal90 give81–99 mm")
            row["criterion"] = "calculated C86.0–86.3 lies within slot range; final pitch-plane offset≤0.20/150, slack2–3%, no tight spot in20 hand turns"
            row["assembly_method"] = "install one #35 40-pitch endless loop; set C≈86.17 in DRV-A60 slots; align pitch planes, set slack, then torque adapter hardware"
            row["inspection_method"] = "centre-distance scale check, straightedge/feeler alignment, midspan slack measurement, twenty locked-out hand rotations"
        elif iid == "IF-008":
            row = assessed(row, [.02, .15], (0, .15), [historical, *refs], kind="OFFICIAL_REFERENCE_DRAWING_AND_RECEIPT_LIMIT_CONTRACT",
                           calculation="pilot diametral clearance0.05–0.15; shaft circle and D-flat clearance0.02–0.10; reported interval spans all controlled gaps")
            row["criterion"] = "pilot diametral clearance0.05–0.15; shaft circle and flat clearance0.02–0.10; M5 hole/PCD within stated receipt limits; D-flat bearing SF≥2"
            row["fit_tolerance"] = "motor pilotØ31.95–32.00 / adapterØ32.05–32.10; shaftØ11.95–12.00 and flat10.85–10.90 / hubØ12.02–12.05 and flat10.92–10.95"
            row["surface_finish"] = "pilot bore Ra≤3.2; D-bore Ra≤1.6; deburr all M5 clearance holes"
            row["assembly_method"] = "accept only the released reference limits; orient D-flat, seat pilot, torque 4×M5, install fuse pin; alternate donor requires DRV-Axx/DRV-F01Axx deviation"
            row["inspection_method"] = "supplier drawing plus receipt micrometer/CMM; blue-check D-flat, hand fit, assembled TIR and physical Gate-1 later"
            row["adjustment_shim_method"] = "reject/remake outside limits; no shim or set-screw-only torque path"
            row["thermal_condition"] = "20°C dimensional digital closure; receipt/Gate-1 physical NOT_RUN; purchase requires user approval"
        elif iid == "IF-009":
            row = assessed(row, [.010, .033], (0, .040), [historical, *refs], kind="DRAWING_OPPOSITE_LIMITS",
                           calculation="gear bore - shaft =0.010–0.033; key side clearance=0.005–0.015 mm")
            row["criterion"] = "diametral clearance0–0.040 and key side clearance0.005–0.015 mm; TS-03 controls loaded phase"
        elif iid == "IF-010":
            row = assessed(row, [-.008, .008], (-.008, .008), [historical, *refs], kind="SKF_NORMAL_AND_H6_LIMITS",
                           calculation="625 bore opposite limit - FM-GA-01 shaft opposite limit = -0.008–+0.008 mm")
            row["criterion"] = "diametral transition fit -0.008–+0.008 mm; receipt gauge and free-rotation check required"
        elif iid == "IF-011":
            row = assessed(row, [0, .096], (0, .100), [historical, *refs], kind="SKF_NORMAL_H7_POM_THERMAL_BOUND_AND_POSITIVE_RETAINER",
                           calculation="23°C clearance=0.000–0.026; at60°C add (130−12)e-6×16×37=0.0699; bound=0.000–0.096 mm; pocket−width=0.100–0.220; cap overlap=0.446–0.500")
            row["criterion"] = "23–60°C diametral clearance0–0.100; axial clearance0.10–0.22; outer-ring overlap≥0.44; assembled roller TIR≤0.10 and no outer-ring creep"
            row["fit_tolerance"] = "seat16.000–16.018 H7 x5.10; bearingOD15.992–16.000 x width4.880–5.000; cap bore15.00–15.10; cap recess1.05"
            row["surface_finish"] = "seat Ra≤1.6 and shoulder square≤0.05; cap flatness≤0.05 and bearing face burr-free"
            row["assembly_method"] = "press outer ring only into each pocket; fit two flush FM-GC-01 caps with SYS-14 balanced through-bolts; do not clamp shields or inner rings"
            row["inspection_method"] = "23±2°C bore/depth/OD gauges; cap blue-check on outer-ring edge only; dial-indicate roller, free-rotate, then witness-mark and check creep"
            row["adjustment_shim_method"] = "reject/remachine if limits miss; no adhesive, printed cap or improvised washer"
            row["thermal_condition"] = "23–60°C calculation using POM-C CLTE13e-5/K and bearing-steel bound12e-6/K; physical hot rotation NOT_RUN"
        elif iid == "IF-012":
            row = assessed(row, [.200, .408], (.180, .450), [historical, *refs], kind="COMPLETE_ASSEMBLY_FUNCTIONAL_ACCEPTANCE",
                           calculation="finished bore opposite limit - h6 axle opposite limit =0.200–0.408 mm")
            row["criterion"] = "0.180–0.450 mm diametral clearance; one axle passes both aligned brackets by hand without visible bending"
            row["assembly_method"] = "leave both T-slot brackets loose; pass the finished axle through both; torque each bracket to2.0 N.m while axle remains free"
            row["inspection_method"] = "plug/bore gauge each bracket; complete-pair hand-pass and roller free-rotation check"
        elif iid == "IF-016":
            row = assessed(row, [-.008, .011], (-.008, .011), [historical, *refs], kind="SKF_NORMAL_AND_H6_LIMITS",
                           calculation="6001 bore opposite limit - SP-SH-01 shaft opposite limit = -0.008–+0.011 mm")
            row["criterion"] = "diametral transition fit -0.008–+0.011 mm; receipt gauge and free-rotation check required"
        elif iid == "IF-017":
            row = assessed(row, [0, .030], (0, .036), [historical, *refs], kind="SKF_NORMAL_H7_POCKET_AND_POSITIVE_RETAINER",
                           calculation="seat−OD=0.000–0.030 mm; pocket−width=0.050–0.220 mm axial clearance; retainer radial overlap=0.9455–1.000 mm")
            row["criterion"] = "diametral clearance0–0.036; axial clearance0.05–0.22; outer-ring overlap≥0.90 mm; no seal/inner-ring contact"
            row["fit_tolerance"] = "seat28.000–28.021 H7 x8.05–8.10; bearingOD27.991–28.000 x width7.880–8.000; retainer relief26.00–26.10"
            row["surface_finish"] = "seat Ra≤1.6 and shoulder square≤0.05; retainer flatness≤0.10 and bearing-side burr-free"
            row["assembly_method"] = "press outer ring only into marked-face pocket against integral shoulder; fit SP-BR-01 with SYS-13 cross pattern; do not shim away axial clearance"
            row["inspection_method"] = "bore/depth gauge and micrometer; blue-check retainer only on outer-ring edge; axial push/pull and free-rotation check"
            row["adjustment_shim_method"] = "reject/remachine if limits miss; no printed retainer or improvised washer"
        elif iid == "IF-018":
            row = assessed(row, [.200, .411], (.180, .450), [historical, *refs], kind="DRAWING_OPPOSITE_LIMITS_AND_CLAMP",
                           calculation="finished adapter bore opposite limit - h6 spindle opposite limit =0.200–0.411 mm")
            row["criterion"] = "0.180–0.450 mm diametral clearance; M6 clamp prevents slip and metal collar carries axial load"
            row["assembly_method"] = "ream, slide onto spindle, seat against metal collar, then torque M6 through clamp to2.5 N.m"
            row["inspection_method"] = "plug/bore gauge; hand slide before clamp; witness-mark and verify no adapter slip after clamp"
        elif iid == "IF-020":
            row = assessed(row, [.300, .350], (.250, .400), [historical, *refs], kind="NSK_51102_ABUTMENT_AND_GENERAL_HOUSING_CLEARANCE",
                           calculation="plate pocket - bearing OD =0.300–0.350 mm diametral; shaft abutment minimum23.00 mm; housing abutment17.20 mm")
            row["criterion"] = "housing diametral clearance>0.25 mm; shaft abutment≥23 mm; housing abutment≤20 mm; shim-set loaded-direction endplay0.05–0.15 mm"
            row["fit_tolerance"] = "Ø15 h6 x11 seat; Ø23.00–23.05 x9 shaft shoulder; pocketØ28.30–28.35 x9.10–9.15; 0.05–0.30 steel shim selection"
            row["surface_finish"] = "seat/pocket Ra≤1.6; both abutment faces square≤0.03 to Datum A; fillet≤R0.3"
            row["assembly_method"] = "fit shaft washer against integral shoulder; cage/housing washer into marked-face pocket; select ground steel shim after bearing-height measurement"
            row["inspection_method"] = "micrometer/bore/depth gauge; blue-check both washer ribs; dial-indicator loaded-direction endplay and free hand rotation"
            row["adjustment_shim_method"] = "0.05–0.30 mm ground steel shim only; reject if target endplay cannot be obtained"
            row["thermal_condition"] = "20°C dimensional screen; loaded and hot physical checks NOT_RUN; donor motor adapter remains IF-008"
        elif iid == "IF-014":
            row = assessed(row, [.200, .259], (.180, .300), [historical, *refs], kind="DRAWING_OPPOSITE_LIMITS",
                           calculation="reamed bore opposite limit - h6 axle opposite limit =0.200–0.259 mm")
            row["criterion"] = "diametral running clearance0.180–0.300 mm and free motion under0.2–1.0 N filament tension"
        elif iid == "IF-015":
            row = assessed(row, [.200, .509], (.180, .550), [historical, *refs], kind="DRAWING_OPPOSITE_LIMITS_AND_PAIR_ALIGNMENT",
                           calculation="end-plate clearance0.200–0.309; carriage clearance0.400–0.509 mm")
            row["criterion"] = "end-plate diametral clearance0.180–0.350; carriage0.350–0.550; TS-12 controls pair parallelism"
            row["assembly_method"] = "match-ream both metal end plates on the two h6 rods; install carriage before final end-plate torque"
            row["inspection_method"] = "micrometer rods; plug/bore gauge; dial-indicator parallelism and full-stroke hand traverse"
        elif iid == "IF-029":
            row = assessed(row, [.50, .70], (.40, .80), [historical, *refs], kind="SELECTED_THROUGH_BOLT_CLEARANCE",
                           calculation="finished hole4.50–4.70 minus M4 maximum major diameter4.00 = diametral clearance0.50–0.70")
            row["criterion"] = "diametral clearance0.40–0.80; PPR-C01 flat-head flush/recessed≤0.05; no heat-set insert route"
            row["fit_tolerance"] = "both holes Ø4.50–4.70; C01 M4x16 90° flat-head + washer/nyloc; C10 2×M4x25 + washers/nyloc"
            row["surface_finish"] = "ream/deburr; C01 underside countersink smooth and head flush"
            row["assembly_method"] = "install only the selected through-bolt routes; hold nut with spanner and torque1.2 N.m"
            row["inspection_method"] = "plug/caliper hole check; C01 straightedge head-flush check; witness marks and full slide/traverse"
            row["adjustment_shim_method"] = "reject/reprint if hole or flushness misses; no heat-set insert substitution"
        elif iid == "IF-028":
            row = assessed(row, [.40, .50], (.30, .60), [historical, *refs], kind="SELECTED_THROUGH_BOLT_CLEARANCE",
                           calculation="finished hole3.40–3.50 minus M3 maximum major diameter3.00 = diametral clearance0.40–0.50 mm")
            row["criterion"] = "diametral clearance0.30–0.60; nuts and washers accessible from open enclosure/control-panel side; no heat-set inserts"
            row["fit_tolerance"] = "both parts finished holes Ø3.40–3.50; C06 4×M3x12 per enclosure; C11 4×M3x16"
            row["surface_finish"] = "ream/deburr both faces; no raised burr under washer"
            row["assembly_method"] = "insert screw from exterior, fit washer and all-metal nut from accessible interior, torque0.5 N.m and witness-mark"
            row["inspection_method"] = "plug/caliper hole check; verify tool access, witness marks, no print cracking and C06 optical alignment"
            row["adjustment_shim_method"] = "reject/reprint if hole misses or boss cracks; no heat-set insert substitution"
        elif iid == "IF-022":
            row = assessed(row, [.050, .102], (.03, .12), [historical, *refs], reason=reason,
                           kind="SELECTED_REFERENCE_DRIVE_COUPLING_CLEARANCE",
                           calculation="FD-CP-01 bore opposite limit − shaft opposite limit =0.050–0.102; auger clearance0.200–0.322; gearbox rating SF=5/2.2=2.273; both spring-pin static screens SF≥2")
            row["criterion"] = "coupling diametral clearance0.03–0.12; auger clearance0.15–0.35; pin/boss and gearbox SF≥2"
            row["fit_tolerance"] = "shaft7.978–8.000 / coupling bores8.050–8.080 / auger bore8.200–8.300; two matched Ø3.00–3.05 cross-holes"
            row["surface_finish"] = "shaft/bore/pin holes deburred Ra≤3.2; no inward food-trap burr"
            row["assembly_method"] = "key EG17-G10 into FD-CP-01; install new upper Ø3x18 and lower SYS-15 Ø3x12 spring pins; bolt FD-DA-01 only to metal frame"
            row["inspection_method"] = "micrometer/pin gauge; ten hand turns; coupling TIR; 2.2 N.m torque-arm and 24 PPR tach tests after receipt"
            row["adjustment_shim_method"] = "reject mismatched holes; replace pin after removal; no adhesive or improvised pin"
        elif iid == "IF-027":
            row = assessed(row, [0, 0], (0, 0), [historical, *refs], kind="REMOVED_FROM_ACTIVE_ARCHITECTURE",
                           calculation="hopper-maintenance PTC, spreader, clamp, power output and purchase line removed; external predry remains")
            row["unit"] = "interfaces"
            row["criterion"] = "zero active hopper-maintenance PTC interfaces"
            row["fit_tolerance"] = "NOT_APPLICABLE — interface removed"
            row["surface_finish"] = "NOT_APPLICABLE — interface removed"
            row["assembly_method"] = "do not install or wire a hopper-maintenance heater; use the frozen external-predry process"
            row["inspection_method"] = "verify active CAD, BOM, I/O schedule and firmware contain no hopper-PTC hardware path"
            row["adjustment_shim_method"] = "NOT_APPLICABLE"
        elif iid == "IF-030":
            schedule = list(csv.DictReader(io.StringIO(source_text("exports/final/bom/fastener_schedule.csv"))))
            assembly = source_text("docs/final/assembly_steps.csv")
            required_fields = ("joint_id", "part_ids", "specification", "quantity", "torque_Nm", "locking", "tool", "inspection", "source", "verification_state")
            qualified = (len(schedule) == 30 and len({item["joint_id"] for item in schedule}) == 30
                         and all(all(item[field] for field in required_fields) for item in schedule)
                         and all(item["joint_id"] in assembly for item in schedule))
            row = assessed(row, [30, 30] if qualified else [None, None], (30, 30), [historical, *refs],
                           reason="" if qualified else "Fastener schedule and assembly-step joint references are not one-to-one complete.",
                           kind="INSTANCE_JOINT_CONTRACT_COVERAGE",
                           calculation="30 unique schedule joint IDs = 30 joint IDs referenced by generated assembly steps; every contract field nonblank")
            row["unit"] = "joints"
            row["criterion"] = "all 30 unique joint contracts have parts/specification/quantity/torque/locking/tool/inspection/source/state and appear in assembly steps"
            row["fit_tolerance"] = "per-joint limits and functional acceptance in fastener_schedule.csv; no aggregate nominal-hole substitution"
            row["assembly_method"] = "kit and sign by joint_id; HOLD states remain HOLD and are not converted by coverage"
            row["inspection_method"] = "machine-check unique/nonblank contracts and one-to-one assembly-step reference; perform each listed physical inspection later"
            row["adjustment_shim_method"] = "joint-specific only; no unlisted washer, insert or fastener substitution"
        elif iid == "IF-024":
            row = assessed(row, [.037, .078], (.030, .090), [historical, *refs], reason=reason,
                           kind="SUPPLIER_CG_AND_H7_LIMITS",
                           calculation="opposite limits: [6.550−6.513,6.565−6.487]=0.037–0.078 mm diametral; radial0.0185–0.0390 mm")
            row["criterion"] = "diametral clearance0.030–0.090; radial clearance≤0.05; metal flange positively retains heater"
            row["fit_tolerance"] = "Ø6.550–6.565 reamed bore / Ø6.487–6.513 Type CG sheath; insertion length39.50±0.20"
            row["surface_finish"] = "reamed bore Ra≤1.6; burr-free lead face; thin high-temperature anti-seize on sheath only"
            row["assembly_method"] = "insert by hand from lead face; secure custom MFR flange with SYS-16; leads remain outside bore"
            row["inspection_method"] = "bore gauge + micrometer/camber report; full hand insertion; cold resistance9.12–10.56 ohm and insulation test"
            row["adjustment_shim_method"] = "reject out-of-limit bore/heater or flange; no sanding, swaging, foil shim or lead loading"
        elif iid == "IF-025":
            row = assessed(row, [.17, .28], (.15, .30), [historical, *refs], reason=reason,
                           kind="MTA1_PROBE_AND_STOP_COLLAR_CONTRACT",
                           calculation="bore minus probe opposite limits=3.20-3.03 to3.25-2.97=0.17-0.28; bottom gap=5.35-5.25 to5.45-5.15=0.10-0.30 mm")
            row["criterion"] = "diametral clearance0.15-0.30; tip gap0.10-0.30; positive metal stop retention; receipt bias<=2 C and t90<=30 s"
            row["fit_tolerance"] = "bore3.20-3.25 depth5.35-5.45 / MTA1 probe2.97-3.03 / tip-to-collar5.15-5.25"
            row["surface_finish"] = "flat-bottom bore Ra<=3.2; burr-free; supplier-welded collar, no field sheath modification"
            row["assembly_method"] = "insert to stop; capture collar with TH-TCR-01 and SYS-17; do not bottom or set-screw the MI sheath"
            row["inspection_method"] = "micrometer/depth gauge; >=100 Mohm at100 VDC; 20 N pull; barrel coupon bias/step-response test"
            row["adjustment_shim_method"] = "reject probe/bore/stop outside limits; no sheath swage, cut, foil shim or deeper bore"
        elif iid == "IF-026":
            row = assessed(row, [.17, .28], (.15, .30), [historical, *refs], reason=reason,
                           kind="MTA1_PROBE_AND_STOP_COLLAR_CONTRACT",
                           calculation="bore minus probe=0.17-0.28; bottom gap=11.95-10.05 to12.05-9.95=1.90-2.10; nearest heater-channel surface gap>=7.47 mm")
            row["criterion"] = "diametral clearance0.15-0.30; bottom gap1.90-2.10; channel ligament>=6.0; positive metal stop retention"
            row["fit_tolerance"] = "bore3.20-3.25 depth11.95-12.05 / MTA1 probe2.97-3.03 / tip-to-collar9.95-10.05"
            row["surface_finish"] = "blind bore Ra<=3.2; burr-free; supplier-welded collar, no field sheath modification"
            row["assembly_method"] = "insert to stop; capture collar with TH-TCR-01 and SYS-17; do not bottom or set-screw the MI sheath"
            row["inspection_method"] = "micrometer/depth gauge and borescope; >=100 Mohm at100 VDC; 20 N pull; die coupon response"
            row["adjustment_shim_method"] = "reject probe/bore/stop outside limits; no sheath swage, cut, foil shim or deeper bore"
        elif iid == "IF-031":
            row = assessed(row, [.10, .16], (.08, .18), [historical, *refs], kind="REGISTERED_FLANGE_OPPOSITE_LIMITS",
                           calculation="socket−spigot diametral clearance=0.10–0.16; downstream housing ID−upstream hopper ID=0.00–0.15; gasket ID clearance to largest flow bore≥0.15 mm")
            row["criterion"] = "register clearance0.08–0.18; nonnegative0–0.15 flow expansion; gasket must not intrude; compressed thickness0.35–0.40"
            row["fit_tolerance"] = "spigot28.77–28.80 / socket28.90–28.93; flow24.90–25.00→25.00–25.05; gasket ID29.20–29.40"
            row["surface_finish"] = "flow bore and flange edges deburred Ra≤3.2; food-contact gasket certificate required"
            row["assembly_method"] = "seat new FD-GSK-01 outside the spigot; engage register without force; tighten four M4 through bolts in cross pattern to measured0.35–0.40 gasket thickness"
            row["inspection_method"] = "bore/micrometer and depth-gauge report; feeler/compressed-thickness check; dry-flake leak and retained-particle inspection under lockout"
        elif iid == "IF-032":
            row = assessed(row, [1.10 - 1.05, 1.70 - .95], (.05, .75), [historical, *refs],
                           calculation="slot opposite limit − sheet opposite limit = 0.05–0.75 mm")
            row["criterion"] = "0.05 ≤ total slot clearance ≤ 0.75 mm; no inward burr/dead pocket"
            row["fit_tolerance"] = "slot1.40±0.30 / sheet1.00±0.05"
            row["surface_finish"] = "sheet edges deburred; printed slot support-free"
        result.append(row)
    assert set(specs) == {r["interface_id"] for r in legacy}, "each historical interface needs reconciliation"
    return result


def main() -> None:
    data = rows()
    assert len({r["interface_id"] for r in data}) == len(data)
    unresolved = [r["interface_id"] for r in data if r["status"] != "PASS"]
    by_id = {r["interface_id"]: r for r in data}
    coverage_ok = (len(data) == 48 and len(by_id) == 48 and not unresolved
                   and by_id.get("IF-030", {}).get("status") == "PASS"
                   and by_id.get("IF-030", {}).get("numeric_status") == "PASS")
    report = {
        "revision": REV, "generator": "calculations/tolerance_stack_final.py",
        "canonical_catalog": str(CSV_OUT.relative_to(ROOT)), "compatibility_mirror": str(MIRROR_OUT.relative_to(ROOT)),
        "legacy_review_commit": LEGACY_COMMIT,
        "method": "source-pinned component bounds; two-sided criteria; null means unknown, not zero",
        "physical_validation_state": "NOT_RUN", "interfaces": data,
        "coverage": {"status": "PASS" if coverage_ok else "HOLD",
                     "claim": "16 mandatory tolerance stacks + all32 historical interface IDs reconciled; IF-030 verifies 30 unique instance-level joint contracts and assembly-step references",
                     "gaps": [] if coverage_ok else ["One or more interface rows or the IF-030 instance-level joint contract map remain unresolved.",
                              "Compatibility TS/IF aliases are not additional coverage."]},
        "pass_count": sum(r["status"] == "PASS" for r in data), "hold_count": sum(r["status"] == "HOLD" for r in data),
        "fail_count": sum(r["status"] == "FAIL" for r in data), "unresolved_interfaces": unresolved,
        "status": "PASS" if coverage_ok else "HOLD",
    }
    JSON_OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=data[0].keys(), lineterminator="\n")
    writer.writeheader(); writer.writerows(data)
    for path in (CSV_OUT, MIRROR_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stream.getvalue(), encoding="utf-8")
    lines = [f"# v0.8 공차·끼워맞춤 검토 — {report['status']}", "",
             "단일 생성원 `calculations/tolerance_stack_final.py`, 지배 catalog `exports/final/interface_catalog.csv`.",
             "`exports/fabrication/interface_catalog.csv`는 byte-identical compatibility mirror이며 별도 authority가 아니다.",
             "임의 IF-01..16을 폐기하고 f3b1e66의 IF-001..032를 실제 원본과 대조했다. 중복 TS/IF는 추가 coverage가 아니다.",
             "unknown은 JSON null/CSV 빈 수치다. 요구범위와 계산 결과를 분리하고 양쪽 한계를 검사한다.",
             f"전체 mating coverage: {report['coverage']['status']}. IF-030의 30개 unique joint contract와 assembly-step 1:1 참조를 함께 검사하며 단순 행 개수만으로 PASS하지 않는다.", "",
             f"PASS {report['pass_count']} / HOLD {report['hold_count']} / FAIL {report['fail_count']}. 물리 NOT_RUN; 구매·제작·통전 USER_APPROVAL_REQUIRED.", ""]
    for r in data:
        lines += [f"## {r['interface_id']} — {r['status']}", "", f"{r['part_a']} ↔ {r['part_b']}", "",
                  f"- 원본 치수: {r['nominal_dimension']}", f"- 계산: {r['calculation']}",
                  f"- 결과: {r['minimum']} … {r['maximum']} {r['unit']} / 요구: {r['criterion']} / numeric {r['numeric_status']}",
                  f"- 미해결: {r['blockers'] or '없음 — 명시된 디지털 범위 한정, 실물 미검증'}"]
        for ref in json.loads(r["source_refs"]):
            prefix = f"{ref['commit'][:12]}:" if ref["commit"] else ""
            lines.append(f"- 근거: `{prefix}{ref['path']}:{ref['line']}` SHA256 `{ref['sha256']}`")
        lines.append("")
    lines += ["Cutter/blade gap은 금속 shim만 사용한다. Cutter/screw/heater/high-current의 물리 검증은 물리 lockout과 사용자 확인 전 완료로 표시하지 않는다. 명시된 디지털 검증 범위의 완료는 물리·제작·운전 승인을 대체하지 않는다.", ""]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"FINAL_TOLERANCE_STACK_{report['status']} interfaces={len(data)} unresolved={len(unresolved)} coverage={report['coverage']['status']}")
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
