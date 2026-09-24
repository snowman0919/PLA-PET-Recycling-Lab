"""Split the historical C1 hopper BRep into bounded PC panels and steel seam straps.

The STEP contains a PC shell only.  The straps are upper-wall seam supports,
not the C1 BOM's unmodeled lower safety liner; liner fit and retention remain
HOLD.  The lid, lid switch seat, and lower cutter opening are not changed.
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

V = cq.Vector
REPO = Path(__file__).resolve().parents[2]
SPLIT_X = 120.0
# The C1 inner loft endpoints are the datum for the two planar inside faces.
Z_IN_LO, Z_IN_HI = 443.502751847084, 501.0
SEAM_Z_LO, SEAM_Z_HI = 456.0, 495.0
BOLT_X = (107.0, 133.0)
BOLT_Z = (465.0, 486.0)
BORE_R = 1.7  # M3 clearance, through PC skin and steel captive-nut bosses


def _inner_y(front: bool, z: float) -> float:
    y0, y1 = (165.4, 178.0) if front else (322.8, 312.0)
    return y0 + (y1-y0) * (z-Z_IN_LO) / (Z_IN_HI-Z_IN_LO)


def _bore(front: bool, x: float, z: float) -> cq.Solid:
    # A short Y-directed drill: never reaches the opposite wall or the mouth.
    return cq.Solid.makeCylinder(BORE_R, 30.0,
                                 V(x, 155.0 if front else 305.0, z), V(0, 1, 0))


def _nut_boss(front: bool, x: float, z: float) -> cq.Solid:
    # M3 captive hex weld-nut representation. It penetrates the strap 0.5 mm
    # to make a continuous steel solid; weld/thread and torque are not rated.
    side = 1.0 if front else -1.0
    base_y = _inner_y(front, z) + side * 1.0
    points = [V(x + 3.18*math.cos(math.tau*i/6), base_y,
                z + 3.18*math.sin(math.tau*i/6)) for i in range(6)]
    wire = cq.Wire.makePolygon(points, close=True)
    return cq.Solid.extrudeLinear(wire, [], V(0, side*3.0, 0))


def _strap(front: bool) -> cq.Solid:
    # A ruled planar 1.5-mm steel strap lies entirely within the cavity,
    # face-contacting the original loft's inner wall without enlarging its
    # external envelope. Its lower edge is 12.5 mm above the cutter inlet.
    side = 1.0 if front else -1.0
    yz = [(z, _inner_y(front, z) + side*d)
          for z, d in ((SEAM_Z_LO, 0), (SEAM_Z_HI, 0),
                       (SEAM_Z_HI, 1.5), (SEAM_Z_LO, 1.5))]
    wire = cq.Wire.makePolygon([V(100.0, y, z) for z, y in yz], close=True)
    strap = cq.Solid.extrudeLinear(wire, [], V(40.0, 0, 0))
    for x in BOLT_X:
        for z in BOLT_Z:
            strap = strap.fuse(_nut_boss(front, x, z))
    for x in BOLT_X:
        for z in BOLT_Z:
            strap = strap.cut(_bore(front, x, z))
    return strap.clean()


def components() -> list[tuple[str, cq.Solid]]:
    """Return two distinct PC print solids and two steel bolted seam straps.

    The split is an exact planar BRep partition, not two copied envelopes.
    Four M3 through-holes per panel connect the PC skin to integral captive
    bosses on the two steel straps (8 screws total).
    """
    original = cq.importers.importStep(str(REPO / "cad/parts/HOPPER.step")).val()
    if len(original.Solids()) != 1 or not original.isValid():
        raise RuntimeError("C1 hopper is not one valid shell solid")
    regions = (cq.Solid.makeBox(SPLIT_X + 1000, 1000, 1000,
                                V(-1000, -300, 0)),
               cq.Solid.makeBox(1120, 1000, 1000,
                                V(SPLIT_X, -300, 0)))
    panels = []
    for name, region, x in zip(("HOPPER_PANEL_L", "HOPPER_PANEL_R"),
                               regions, (BOLT_X[0], BOLT_X[1])):
        panel = original.intersect(region)
        for front in (True, False):
            for z in BOLT_Z:
                panel = panel.cut(_bore(front, x, z))
        panel = panel.clean()
        if len(panel.Solids()) != 1 or not panel.isValid():
            raise RuntimeError(f"{name} is not one valid PC solid")
        b = panel.BoundingBox()
        if max(b.xlen, b.ylen, b.zlen) > 210.0 + 1e-6:
            raise RuntimeError(f"{name} exceeds 210 mm printer axis")
        panels.append((name, panel))
    straps = [("HOPPER_SEAM_FRONT", _strap(True)),
              ("HOPPER_SEAM_REAR", _strap(False))]
    for name, strap in straps:
        if len(strap.Solids()) != 1 or not strap.isValid():
            raise RuntimeError(f"{name} is not one valid steel solid")
    whole = original.BoundingBox()
    joined = cq.Compound.makeCompound([shape for _, shape in panels]).BoundingBox()
    if any(abs(getattr(whole, edge)-getattr(joined, edge)) > 1e-5
           for edge in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")):
        raise RuntimeError("split PC panels changed the C1 exterior envelope")
    if SEAM_Z_LO <= whole.zmin + 10 or SEAM_Z_HI >= whole.zmax - 4:
        raise RuntimeError("steel seam enters cutter inlet or lid closure")
    for strap_name, strap in straps:
        for panel_name, panel in panels:
            gap = BRepExtrema_DistShapeShape(strap.wrapped, panel.wrapped).Value()
            if gap > 1e-4 or strap.intersect(panel).Volume() > 1e-4:
                raise RuntimeError(f"{strap_name}/{panel_name} seam fit invalid")
    return panels + straps
