#!/usr/bin/env python3
"""외부 plotting 의존성 없이 핵심 시나리오 SVG를 생성한다."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "simulation" / "openmodelica" / "results" / "raw"
OUT = ROOT / "simulation" / "openmodelica" / "results" / "plots"


def rows(name: str) -> list[dict[str, float]]:
    with (RAW / f"{name}_res.csv").open(newline="") as stream:
        return [{k: float(v) if v.lower() not in {"true", "false"} else float(v.lower() == "true") for k, v in r.items()} for r in csv.DictReader(stream)]


def svg_plot(name: str, series: list[tuple[str, str]], ylabel: str) -> None:
    data = rows(name)
    width, height, pad = 900, 460, 58
    xmax = max(r["time"] for r in data)
    ymax = max(abs(r[key]) for r in data for _, key in series) * 1.1 or 1
    colors = ["#146c94", "#c0392b", "#558b2f", "#7b1fa2"]
    paths = []
    for index, (label, key) in enumerate(series):
        points = []
        for row in data:
            x = pad + row["time"] / xmax * (width - 2 * pad)
            y = height - pad - row[key] / ymax * (height - 2 * pad)
            points.append(f"{x:.1f},{y:.1f}")
        paths.append(f'<polyline fill="none" stroke="{colors[index]}" stroke-width="2" points="{" ".join(points)}"/>')
        paths.append(f'<text x="{pad+index*190}" y="24" fill="{colors[index]}" font-size="15">{label}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white"/><line x1="{pad}" y1="{height-pad}" x2="{width-pad}" y2="{height-pad}" stroke="#222"/><line x1="{pad}" y1="{pad}" x2="{pad}" y2="{height-pad}" stroke="#222"/>
<text x="{width/2}" y="{height-12}" text-anchor="middle">time [s]</text><text x="16" y="{height/2}" transform="rotate(-90 16 {height/2})" text-anchor="middle">{ylabel}</text>
{''.join(paths)}</svg>'''
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.svg").write_text(svg)


def main() -> None:
    svg_plot("ReverseClear", [("estimated cutter torque", "estimatedCutterTorque"), ("fuse torque", "inputFuse.transmittedTorque"), ("duty", "dutyCommand")], "torque / duty")
    svg_plot("MechanicalFuseTrip", [("estimated cutter torque", "estimatedCutterTorque"), ("fuse torque", "inputFuse.transmittedTorque")], "torque [N m]")
    svg_plot("HotExtrusionJamPLA", [("zone 1", "T1"), ("zone 2", "T2"), ("zone 3", "T3"), ("die", "Tdie")], "temperature [degC]")
    svg_plot("GaugeDropout", [("line tension", "lineTension")], "tension [N]")
    svg_plot("FullSystemPLA", [("bus power", "busPower"), ("net flow", "extruder.netFlowGPH")], "power [W] / flow [g/h]")
    svg_plot("FullSystemJam", [("cutter torque", "shredder.estimatedCutterTorque"), ("motor current", "shredder.motor.current")], "torque [N m] / current [A]")
    print("OPENMODELICA_PLOTS_OK count=6")


if __name__ == "__main__":
    main()
