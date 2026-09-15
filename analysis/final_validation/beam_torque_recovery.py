"""Measured root torque for the existing straight X-axis RECT B31 surrogate.

The applied torque is used only as an equilibrium check, never as a result.
This extractor does not qualify a real keyed shaft or a physical drive datum.
"""
from __future__ import annotations
import math
import re
from pathlib import Path

NUMBER = re.compile(r"[-+]?\d*\.?\d+(?:[EeDd][-+]?\d+)?")

def expanded_root_torque(path: Path, applied_nm: float, root_x_m=0.0):
    if not math.isfinite(applied_nm) or not math.isfinite(root_x_m):
        raise ValueError("non-finite torque or datum")
    coordinates, forces = {}, {}
    coord_mode = force_mode = False
    for line in Path(path).read_text(errors="strict").splitlines():
        if line.startswith("    2C"):
            coord_mode = True
            continue
        if line.startswith(" -4"):
            force_mode = "FORC" in line
            if force_mode:
                forces = {}
            continue
        if line.startswith(" -3"):
            coord_mode = force_mode = False
            continue
        if not line.startswith(" -1") or not (coord_mode or force_mode):
            continue
        fields = NUMBER.findall(line)
        if len(fields) < 5:
            raise ValueError("truncated FRD vector")
        node = int(fields[1])
        values = tuple(float(v.replace("D","E").replace("d","e")) for v in fields[2:5])
        if not all(math.isfinite(v) for v in values):
            raise ValueError("non-finite FRD vector")
        (coordinates if coord_mode else forces)[node] = values
    root = {n:xyz for n,xyz in coordinates.items() if abs(xyz[0]-root_x_m) <= 1e-10}
    if len(root) != 4 or not set(root) <= set(forces):
        raise ValueError("expected four measured RECT B31 root nodes")
    torque = sum(y*forces[n][2]-z*forces[n][1] for n,(_,y,z) in root.items())
    residual = torque + applied_nm
    tolerance = max(1e-4, abs(applied_nm)*1e-5)
    if not math.isfinite(torque) or abs(residual) > tolerance:
        raise ValueError(f"root torque imbalance: {residual:.9g} N.m")
    return {"measured_torque_nm": torque, "applied_torque_nm": applied_nm,
            "residual_nm": residual, "tolerance_nm": tolerance,
            "root_nodes": sorted(root), "status": "PASS",
            "scope": "measured RF moment at expanded X-axis RECT B31 drive root"}

def add_measured_root_torque(reaction: dict, frd: Path, applied_nm: float):
    measured = expanded_root_torque(frd, applied_nm)
    result = dict(reaction)
    moment = list(reaction["moment_about_origin_nm"])
    # The unexpanded nodes all lie on X, so their r x F has no X component.
    if abs(moment[0]) > 1e-8:
        raise ValueError("unexpected off-axis surrogate; do not double-count couples")
    moment[0] += measured["measured_torque_nm"]
    result.update(moment_about_origin_nm=moment, measured_root_torque=measured,
                  torsional_reaction_qualified=True,
                  reaction_couple_source="Measured expanded FRD root r-cross-RF; not copied input torque",
                  assembly_load_path_qualified=False)
    return result
