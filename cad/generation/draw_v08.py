#!/usr/bin/env python3
"""v0.8 drawing register용 실제 B-Rep 벡터 투영을 생성한다."""

from __future__ import annotations

import html
import sys
from pathlib import Path

import Part

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from cad.freecad.compact.generate import _projection_polylines  # noqa: E402
from cad.freecad.final_v08.generate import final_objects  # noqa: E402

OUT = ROOT / "docs/drawings/v0.8"


def main() -> None:
    items = final_objects()
    groups = {
        "GA-001_general_arrangement": lambda i: True,
        "ASM-001_full_assembly": lambda i: True,
        "ASM-002_module_arrangement": lambda i: i["group"] in {"shredder", "feed", "extruder", "forming", "spooler"},
        "FR-001_frame": lambda i: i["group"] == "frame",
        "SH-001_shredder_assembly": lambda i: i["group"] == "shredder",
        "SH-002_cutter_stack": lambda i: i["name"].startswith(("Hook", "Shaft", "CutterPlate", "M6Fastener")),
        "SH-003_shaft_bearing": lambda i: i["name"].startswith(("Shaft", "Bearing")),
        "SH-004_chain_phase_gear": lambda i: any(t in i["name"] for t in ("Gear", "Sprocket", "Chain", "Drive")),
        "FD-001_hopper": lambda i: "Hopper" in i["name"] or i["group"] == "input",
        "FD-002_recirculation_screen": lambda i: any(t in i["name"] for t in ("Screen", "Flake", "AntiReach")),
        "FD-003_positive_feeder": lambda i: i["group"] == "feed",
        "EX-001_extruder_assembly": lambda i: i["group"] == "extruder",
        "EX-002_screw_barrel_die": lambda i: any(t in i["name"] for t in ("Screw", "Barrel", "Die")),
        "EX-003_heater_thermocouple": lambda i: any(t in i["name"] for t in ("Heater", "TemperatureProbe", "ThermalFuse")),
        "FM-001_cooling_strand_path": lambda i: i["group"] == "forming",
        "FM-002_gauge_puller": lambda i: any(t in i["name"] for t in ("Gauge", "Puller")),
        "SP-001_spooler_traverse": lambda i: i["group"] == "spooler",
        "GD-001_guards_panels": lambda i: any(t in i["name"] for t in ("Guard", "Shield", "Panel", "Bezel")),
        "EL-001_electrical_enclosure": lambda i: i["group"] == "control",
        "SV-001_service_envelopes": lambda i: i["group"] in {"frame", "shredder", "extruder", "control"},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for drawing, predicate in groups.items():
        selected = [i for i in items if predicate(i)]
        shape = Part.makeCompound([i["shape"] for i in selected])
        bb = shape.BoundBox
        views = (
            _projection_polylines(shape, ("x", "y"), (25, 90, 335, 245)),
            _projection_polylines(shape, ("x", "z"), (390, 90, 335, 245)),
            _projection_polylines(shape, ("y", "z"), (755, 90, 335, 245)),
        )
        title = html.escape(drawing.replace("_", " "))
        (OUT / f"{drawing}.svg").write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="520" viewBox="0 0 1123 520">
<rect width="1123" height="520" fill="white"/><rect x="8" y="8" width="1107" height="504" fill="none" stroke="#111" stroke-width="2"/>
<g font-family="Noto Sans CJK KR,sans-serif" fill="#111"><text x="24" y="42" font-size="23" font-weight="bold">{title}</text>
<text x="24" y="68" font-size="14">v0.8 · mm · 제3각법 · source: FreeCAD Python · bodies {len(selected)}</text>
<text x="35" y="110" font-size="14">TOP X-Y</text>{views[0]}<text x="400" y="110" font-size="14">FRONT X-Z</text>{views[1]}<text x="765" y="110" font-size="14">SIDE Y-Z</text>{views[2]}
<text x="24" y="475" font-size="15">Overall X {bb.XLength:.2f} · Y {bb.YLength:.2f} · Z {bb.ZLength:.2f} mm · 치수/공차는 개별 제작도면과 interface catalog 우선</text>
<text x="24" y="498" font-size="13">Revision final-design-fabrication-closure-v0.8 · physical validation NOT_RUN</text></g></svg>\n''', encoding="utf-8")
    print(f"V08_VECTOR_DRAWING_OK count={len(groups)}")


if __name__ == "__main__":
    main()
