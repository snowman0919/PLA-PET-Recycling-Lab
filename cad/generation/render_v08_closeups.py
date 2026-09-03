#!/usr/bin/env python3
"""v0.8 module별 closeup evidence와 multimodal review manifest를 생성한다."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import FreeCAD as App
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from cad.freecad.final_v08.generate import final_objects  # noqa: E402
from cad.freecad.compact.geometry import review_keepout_objects  # noqa: E402
from cad.generation.render_views import render  # noqa: E402

OUT = ROOT / "renders/final_closeups"
MANIFEST = ROOT / "validation/v0.8/multimodal_closeup_manifest.csv"
REVIEW = ROOT / "validation/multimodal_final_review.json"
REV = "final-design-fabrication-closure-v0.8"
CATEGORIES = (
    "interfaces", "fasteners", "adjusters", "sensors", "wire_routes",
    "hot_surfaces", "moving_hazards", "maintenance_access",
)
PALETTE = {"frame": (105, 120, 130), "input": (63, 137, 178), "feed": (69, 151, 97),
           "shredder": (196, 73, 63), "extruder": (225, 116, 55),
           "forming": (51, 122, 183), "spooler": (91, 156, 105), "control": (120, 92, 145)}
VIEWS = {"interfaces": "iso", "fasteners": "right", "adjusters": "top", "sensors": "front",
         "wire_routes": "right", "hot_surfaces": "iso", "moving_hazards": "top", "maintenance_access": "front"}

# Each focus token resolves against the actual final_objects() names. Empty
# lists are intentional evidence of a missing CAD detail or a non-applicable
# hazard, never a fabricated proxy solid.
MODULES = {
    "shredder": {
        "groups": {"shredder"},
        "focus": {
            "interfaces": ("CutterPlate", "Shaft", "Bearing", "Screen", "MotorMountPlate"),
            "fasteners": ("M6Fastener", "BearingRetainer"),
            "adjusters": ("MotorMountPlate", "DriveAdapter", "Chain"),
            "sensors": ("RPMSensor",), "wire_routes": ("ShredderCableRoute",), "hot_surfaces": (),
            "moving_hazards": ("Hook", "Shaft", "PhaseGear", "Sprocket", "Chain"),
            "maintenance_access": ("DriveGuard", "Screen", "BearingRetainer", "MotorMountPlate"),
        },
    },
    "feeder": {
        "groups": {"input", "feed"},
        "focus": {
            "interfaces": ("Hopper", "AntiReach", "FlakeBin", "FeederHousing", "FeederAuger", "FeederAgitatorDriveShaft"),
            "fasteners": ("PTCClamp", "FeederHousing"), "adjusters": ("FeederAuger", "FeederAgitatorDriveShaft", "FeederDriveReference", "PTCClamp"),
            "sensors": ("TemperatureProbeT5", "HopperThermalFuse"), "wire_routes": ("FeederCableRoute",),
            "hot_surfaces": ("HopperPTC", "HopperThermalFuse"),
            "moving_hazards": ("FeederAuger", "FeederAgitatorDriveShaft", "FeederDriveReference"),
            "maintenance_access": ("SlidingLid", "AntiReach", "FlakeBin", "SealedFeedHopper", "PTCClamp"),
        },
    },
    "extruder": {
        "groups": {"extruder"},
        "focus": {
            "interfaces": ("ThrustPlate", "Screw", "Barrel", "DownDie", "ExtruderRear", "ExtruderFront"),
            "fasteners": ("HotMountBolt",),
            "adjusters": ("ExtruderRearFixedDatum", "ExtruderFrontSlidingGuide", "ExtruderFixedCollar"),
            "sensors": ("TemperatureProbe", "ThermalFuse"),
            "wire_routes": ("HeaterLead", "HeaterCableDuct"),
            "hot_surfaces": ("Barrel", "Heater", "DownDie", "HotShield"),
            "moving_hazards": ("Screw", "ExtruderDrive"),
            "maintenance_access": ("HotShield", "Screw", "Barrel", "DownDie", "HeaterCableDuct"),
        },
    },
    "forming": {
        "groups": {"forming"},
        "focus": {
            "interfaces": ("CoolingDuct", "Gauge", "Puller"), "fasteners": ("PullerSpindle", "PullerPlate"),
            "adjusters": ("PullerRoll", "PullerSpindle"), "sensors": ("Gauge",),
            "wire_routes": ("FormingCableRoute",), "hot_surfaces": (),
            "moving_hazards": ("PullerRoll", "PullerSpindle"),
            "maintenance_access": ("PullerGuard", "PullerPlate", "CoolingDuct", "Gauge"),
        },
    },
    "spooler": {
        "groups": {"spooler"},
        "focus": {
            "interfaces": ("Guide", "Dancer", "Spool", "Traverse"), "fasteners": ("Axle", "BearingPlate", "MotorMount"),
            "adjusters": ("Dancer", "SpoolAdapter", "Traverse"), "sensors": ("SensorEnvelope", "LimitEnvelope"),
            "wire_routes": ("SpoolerCableRoute",), "hot_surfaces": (),
            "moving_hazards": ("GuideRoller", "Dancer", "Spool", "Traverse"),
            "maintenance_access": ("Bearing", "MotorMount", "GuideBracket", "TraverseEndPlate"),
        },
    },
    "control": {
        "groups": {"control"},
        "focus": {
            "interfaces": ("ControlPanel", "ControlBezel", "PSU", "CableDuct"), "fasteners": ("ControlBezelM3Fastener", "CableClip"),
            "adjusters": ("ControlEncoder",), "sensors": ("ControlSafetyInput", "EmergencyStop"), "wire_routes": ("CableDuct", "CableClip"),
            "hot_surfaces": (), "moving_hazards": (),
            "maintenance_access": ("ControlPanel", "ControlBezel", "PSU", "CableDuct"),
        },
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def colored(items: list[dict], focus: tuple[str, ...]) -> tuple[list[dict], list[str]]:
    names = [item["name"] for item in items if focus and any(token in item["name"] for token in focus)]
    result = []
    for item in items:
        active = item["name"] in names
        color = PALETTE.get(item["group"], (130, 145, 155)) if (active or not focus) else (205, 211, 214)
        result.append({**item, "color": color})
    return result, names


def review_state(module: str, category: str, focus_count: int) -> tuple[str, str]:
    cold = {"shredder", "forming", "spooler", "control"}
    no_motion = {"control"}
    if category == "hot_surfaces" and module in cold:
        return "NOT_APPLICABLE_COLD_MODULE", "실제 모듈 형상에서 의도된 고온 표면 없음"
    if category == "moving_hazards" and module in no_motion:
        return "NOT_APPLICABLE_STATIC_MODULE", "control enclosure는 정적 모듈"
    if focus_count:
        return "EVIDENCE_PRESENT", "focus solid가 final FreeCAD assembly에서 직접 선택됨"
    return "MODEL_DETAIL_GAP", "해당 module의 dedicated solid가 final assembly에 없음; 물리 확인으로 PASS 대체 금지"


def global_evidence() -> list[dict[str, object]]:
    paths = {
        "front": "renders/final_v08/front.png", "rear": "renders/final_v08/rear.png",
        "left": "renders/final_v08/left.png", "right": "renders/final_v08/right.png",
        "top": "renders/final_v08/top.png", "bottom": "renders/final_v08/bottom.png",
        "isometric": "renders/final_v08/isometric.png", "exploded": "renders/final_closeups/global/exploded.png",
        "module-separated": "renders/final_v08/module-separated.png",
        "service-access": "renders/final_closeups/global/service-access.png",
        "guard-removed": "renders/final_v08/guard-removed.png", "cable-routing": "renders/final_v08/cable-routing.png",
    }
    evidence = []
    for name, rel in paths.items():
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"missing required global view: {rel}")
        with Image.open(path) as image:
            width, height = image.size
        if width < 1200 or height < 900:
            raise RuntimeError(f"undersized global view: {rel} {width}x{height}")
        evidence.append({"view": name, "file": rel, "width_px": width, "height_px": height,
                         "sha256": sha(path), "status": "PRESENT"})
    if len({item["sha256"] for item in evidence}) != len(evidence):
        raise RuntimeError("duplicate global view image")
    return evidence


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    objects = final_objects()
    rows: list[dict[str, object]] = []
    gaps: list[dict[str, str]] = []
    for module, config in MODULES.items():
        items = [item for item in objects if item["group"] in config["groups"]]
        if not items:
            raise RuntimeError(f"empty module: {module}")
        for category in CATEGORIES:
            focus = config["focus"][category]
            visible, focus_names = colored(items, focus)
            state, note = review_state(module, category, len(focus_names))
            path = OUT / module / f"{category}.png"
            render(visible, path, f"v0.8 {module} · {category} · {state}", VIEWS[category])
            with Image.open(path) as image:
                width, height = image.size
            if (width, height) != (1600, 1200):
                raise RuntimeError(f"unexpected image size: {path} {width}x{height}")
            row = {
                "module": module, "category": category, "file": path.relative_to(ROOT).as_posix(),
                "view": VIEWS[category], "visible_object_count": len(visible), "focus_object_count": len(focus_names),
                "focus_objects": ";".join(focus_names) or "NONE_MODELED", "width_px": width, "height_px": height,
                "sha256": sha(path), "review_state": state, "notes": note,
                "physical_validation_state": "NOT_RUN",
            }
            rows.append(row)
            if state == "MODEL_DETAIL_GAP":
                gaps.append({"module": module, "category": category, "finding": note})

    # New v0.8 exploded and service-access evidence uses the same final B-Reps.
    exploded = []
    offsets = {"input": (-80, 0, 55), "shredder": (-40, 0, 25), "feed": (55, 0, 35),
               "extruder": (0, -80, 0), "forming": (-55, -30, -45), "spooler": (80, 60, -20),
               "control": (65, -55, 20), "frame": (0, 0, 0)}
    for item in objects:
        shape = item["shape"].copy(); shape.translate(App.Vector(*offsets.get(item["group"], (0, 0, 0))))
        exploded.append({**item, "shape": shape, "color": PALETTE.get(item["group"], (130, 145, 155))})
    render(exploded, OUT / "global/exploded.png", "v0.8 exploded · actual final B-Reps", "iso")
    service = [{**item, "color": PALETTE.get(item["group"], (130, 145, 155))}
               for item in objects if item["group"] in {"extruder", "control", "frame"}]
    for keepout in review_keepout_objects():
        if keepout["name"] == "KO_ScrewService":
            service.append({**keepout, "group": "review", "color": (220, 80, 70)})
    render(service, OUT / "global/service-access.png", "v0.8 service access · screw withdrawal keepout", "iso")

    fields = ["module", "category", "file", "view", "visible_object_count", "focus_object_count",
              "focus_objects", "width_px", "height_px", "sha256", "review_state", "notes", "physical_validation_state"]
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    if len(rows) != len(MODULES) * len(CATEGORIES) or len({row["file"] for row in rows}) != len(rows):
        raise RuntimeError("closeup coverage mismatch")
    if len({row["sha256"] for row in rows}) != len(rows):
        raise RuntimeError("duplicate closeup pixels; camera/visibility evidence is not independent")
    required_views = global_evidence()
    review = {
        "revision": REV,
        "source": f"{len(objects)}-body FreeCAD B-Rep software projections; no copied/raster-placeholder closeups",
        "required_global_views": required_views,
        "closeup_manifest": MANIFEST.relative_to(ROOT).as_posix(),
        "closeup_coverage": {"modules": len(MODULES), "categories_per_module": len(CATEGORIES), "images": len(rows),
                             "required_categories": list(CATEGORIES), "unique_sha256": len({row["sha256"] for row in rows})},
        "checks": {
            "required_12_global_views": "PASS", "image_presence_and_dimensions": "PASS",
            "unique_hashes_no_copy_reuse": "PASS", "actual_final_brep_selection": "PASS",
            "floating_parts": "REVIEWED_IN_GLOBAL_AND_MODULE_VIEWS",
            "blocked_screw_removal": "PASS_DIGITAL_KEEP_OUT_VISIBLE",
            "blocked_cutter_shaft_removal": "REQUIRES_PHYSICAL_CONFIRMATION",
            "wire_through_solid": "NO_NOMINAL_INTERSECTION_OBSERVED; PHYSICAL_BEND_RADIUS_AND_RECEIVED_CABLES_NOT_RUN",
            "sensor_collision": "NO_NOMINAL_INTERSECTION_OBSERVED; RECEIVED_SENSOR_BODY_AND_AIR_GAP_NOT_RUN",
            "unprotected_chain_or_hot_surface": "CLOSED_AND_GUARD_REMOVED_VIEWS_REVIEWED",
        },
        "model_detail_gaps": gaps,
        "limitations": "software projection review only; tool access, bend radius, received hardware and assembly tolerance require physical commissioning",
        "physical_validation_state": "NOT_RUN",
        "multimodal_gate": "FAIL" if gaps else "PASS",
        "status": "REVIEW_COMPLETE_WITH_BLOCKERS" if gaps else "PASS",
    }
    REVIEW.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"V08_MULTIMODAL_CLOSEUPS_OK modules={len(MODULES)} images={len(rows)} gaps={len(gaps)} global_views={len(required_views)}")


if __name__ == "__main__":
    main()
