#!/usr/bin/env python3
"""v0.8 최종 조립체의 표준 검토 렌더를 생성한다."""

from __future__ import annotations

import sys
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from cad.freecad.final_v08.generate import final_objects  # noqa: E402
from cad.generation.render_views import render  # noqa: E402

OUT = ROOT / "renders/final_v08"


def colored(items):
    palette = {"frame": (105, 120, 130), "shredder": (196, 73, 63), "extruder": (225, 116, 55), "forming": (51, 122, 183), "spooler": (91, 156, 105), "control": (120, 92, 145)}
    return [{**item, "color": item.get("color", palette.get(item.get("group"), (130, 145, 155)))} for item in items]


def transformed(items, axis, angle):
    result = []
    for item in items:
        shape = item["shape"].copy(); shape.rotate(App.Vector(235, 350, 465), axis, angle)
        result.append({**item, "shape": shape})
    return result


def main() -> None:
    items = colored(final_objects())
    views = {
        "front": (items, "front"), "rear": (transformed(items, App.Vector(0, 0, 1), 180), "front"),
        "right": (items, "right"), "left": (transformed(items, App.Vector(0, 0, 1), 180), "right"),
        "top": (items, "top"), "bottom": (transformed(items, App.Vector(1, 0, 0), 180), "top"),
        "isometric": (items, "iso"),
    }
    for name, (objects, view) in views.items():
        render(objects, OUT / f"{name}.png", f"v0.8 final assembly · {name}", view)
    separated = []
    offsets = {"shredder": -180, "input": -90, "feed": 0, "extruder": 90, "forming": 180, "spooler": 270}
    for item in items:
        shape = item["shape"].copy(); shape.translate(App.Vector(offsets.get(item["group"], 0), 0, 0))
        separated.append({**item, "shape": shape})
    render(separated, OUT / "module-separated.png", "v0.8 module-separated interfaces", "iso")
    render([i for i in items if "Guard" not in i["name"] and i["name"] != "HotShield"], OUT / "guard-removed.png", "v0.8 guard removed · inspection only", "iso")
    render([i for i in items if i["group"] in {"extruder", "frame"}], OUT / "hot-zone-service.png", "v0.8 rear datum + front sliding guide", "iso")
    render([i for i in items if i["group"] in {"forming", "spooler"}], OUT / "forming-service.png", "v0.8 gauge/puller/dancer/spool service", "iso")
    render([i for i in items if any(token in i["name"] for token in ("Cable", "Lead", "Control", "PSU"))], OUT / "cable-routing.png", "v0.8 cable routing", "iso")
    print(f"V08_RENDER_OK count={len(list(OUT.glob('*.png')))}")


if __name__ == "__main__":
    main()
