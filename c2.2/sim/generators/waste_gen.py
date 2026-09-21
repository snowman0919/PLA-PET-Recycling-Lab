"""I2 deterministic waste taxonomy generator (stdlib + numpy only).

Classes: W1 layered print (2-4 walls, partial infill, XY-strong/Z-weak),
W2 dense print, W3 fused purge tower (reduced anisotropy), W4 dense purge
blob (near-bulk, worst-case torque/jam flag), P0 spaghetti strand bundle
(wrap-risk metric, NO fracture claim), P1 fused bundle, P2 dense lump
(torque/jam stress flag).

Usage: python3 waste_gen.py --seed N --class W1 [--family flat_plate]
Emits JSON metadata. Exit 2 on admissibility REJECT or invalid inputs.

Evidence: UNCALIBRATED_DIGITAL_SENSITIVITY everywhere. Densities
(PLA 1.24 / PET 1.38 / TPU 1.21 g/cc) are named ASSUMPTIONS. thermal_history
index in [0,1] is an UNCERTAINTY prior, never crystallinity. No fracture,
torque, or jam prediction is claimed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from bonds import (BondGraph, lattice_graph, strengths_for_class,  # noqa: E402
                   require_calibrated_strength)

HERE = Path(__file__).resolve()

# Admissibility box (c2.2/configs/hopper_admissibility.json).
_ADM = json.loads((HERE.parents[2] / "configs"
                   / "hopper_admissibility.json").read_text())
MAX_DX, MAX_DY, MAX_DZ = (float(v) for v in
                          _ADM["max_admissible_bounding_dims_mm"].values())
MARGIN_MM = float(_ADM["admissibility_rule"]["clearance_margin_mm"]["value"])

EVIDENCE = "UNCALIBRATED_DIGITAL_SENSITIVITY"

# Densities are named ASSUMPTIONS (g/cc == g/cm^3).
DENSITIES = {"PLA": (1.24, "ASSUMPTION"), "PET": (1.38, "ASSUMPTION"),
             "TPU": (1.21, "ASSUMPTION")}

# Geometry families: footprint ranges in mm (dx, dy, dz sampled within).
FAMILIES = {
    "flat_plate": {"dx": (60.0, 130.0), "dy": (40.0, 100.0), "dz": (4.0, 12.0)},
    "hollow_box": {"dx": (50.0, 120.0), "dy": (40.0, 100.0), "dz": (20.0, 57.0)},
    "l_bracket": {"dx": (60.0, 130.0), "dy": (40.0, 100.0), "dz": (15.0, 50.0)},
    "curved_shell": {"dx": (60.0, 130.0), "dy": (40.0, 100.0), "dz": (10.0, 40.0)},
    "ribbed": {"dx": (60.0, 120.0), "dy": (40.0, 90.0), "dz": (12.0, 45.0)},
    "failed_print_mass": {"dx": (50.0, 110.0), "dy": (35.0, 85.0),
                          "dz": (15.0, 50.0)},
    "purge_bundle": {"dx": (40.0, 100.0), "dy": (30.0, 80.0),
                     "dz": (15.0, 55.0)},
    "dense_blob": {"dx": (30.0, 80.0), "dy": (25.0, 70.0), "dz": (15.0, 50.0)},
}

CLASS_FAMILIES = {
    "W1": ["flat_plate", "hollow_box", "l_bracket", "curved_shell", "ribbed"],
    "W2": ["flat_plate", "hollow_box", "l_bracket", "ribbed"],
    "W3": ["purge_bundle", "ribbed"],
    "W4": ["dense_blob", "purge_bundle"],
    "P0": ["failed_print_mass", "purge_bundle"],
    "P1": ["failed_print_mass", "purge_bundle"],
    "P2": ["dense_blob", "failed_print_mass"],
}

# (walls, infill_kind, infill_lo, infill_hi, porosity_lo, porosity_hi, raster)
CLASS_STACK = {
    "W1": {"walls": (2, 4), "infill": "grid/tri",
           "infill_range": (0.10, 0.30), "porosity": (0.55, 0.80),
           "raster": "0/90 alternating"},
    "W2": {"walls": (4, 6), "infill": "grid/tri dense",
           "infill_range": (0.60, 0.95), "porosity": (0.05, 0.30),
           "raster": "0/90 alternating"},
    "W3": {"walls": (3, 5), "infill": "concentric fused",
           "infill_range": (0.50, 0.85), "porosity": (0.10, 0.35),
           "raster": "tower-stacked, reduced anisotropy"},
    "W4": {"walls": (0, 0), "infill": "near-bulk",
           "infill_range": (0.95, 1.00), "porosity": (0.00, 0.05),
           "raster": "isotropic-ish purge mass"},
    "P0": {"walls": (1, 1), "infill": "loose strands",
           "infill_range": (0.05, 0.20), "porosity": (0.70, 0.95),
           "raster": "random strand lay"},
    "P1": {"walls": (1, 2), "infill": "fused strands",
           "infill_range": (0.35, 0.65), "porosity": (0.25, 0.55),
           "raster": "partially fused strand mat"},
    "P2": {"walls": (0, 0), "infill": "near-bulk",
           "infill_range": (0.95, 1.00), "porosity": (0.00, 0.05),
           "raster": "isotropic-ish dense lump"},
}

CLASS_FLAGS = {
    "W1": [], "W2": [], "W3": ["reduced_anisotropy"],
    "W4": ["worst_case_torque_jam"],
    "P0": ["wrap_risk", "no_fracture_claim"],
    "P1": ["wrap_risk"], "P2": ["torque_jam_stress"],
}

LAYER_H_MM = 0.2  # nominal layer height (ASSUMPTION, print-process prior)
NOZZLE_MM = 0.4  # nominal extrusion width (ASSUMPTION)


class OversizeError(ValueError):
    pass


def check_admissible(dx: float, dy: float, dz: float) -> None:
    if dx > MAX_DX or dy > MAX_DY or dz > MAX_DZ:
        raise OversizeError(
            f"REJECT: AABB ({dx:.1f},{dy:.1f},{dz:.1f}) exceeds box "
            f"({MAX_DX:.1f},{MAX_DY:.1f},{MAX_DZ:.1f}) mm "
            f"(margin {MARGIN_MM} mm, ASSUMPTION)")


def random_quaternion(rng: np.random.Generator) -> list[float]:
    u = rng.random(3)
    q = [math.sqrt(1 - u[0]) * math.sin(2 * math.pi * u[1]),
         math.sqrt(1 - u[0]) * math.cos(2 * math.pi * u[1]),
         math.sqrt(u[0]) * math.sin(2 * math.pi * u[2]),
         math.sqrt(u[0]) * math.cos(2 * math.pi * u[2])]
    n = math.sqrt(sum(v * v for v in q))
    return [v / n for v in q]


def generate(cls: str, seed: int, family: str | None = None,
             material: str = "PLA") -> dict:
    if cls not in CLASS_FAMILIES:
        raise ValueError(f"unknown class {cls!r}")
    if material not in DENSITIES:
        raise ValueError(f"unknown material {material!r}")
    fams = CLASS_FAMILIES[cls]
    fam = family or fams[seed % len(fams)]
    if fam not in fams:
        raise ValueError(f"family {fam!r} not in class {cls} set {fams}")
    rng = np.random.default_rng(seed * 7919 + len(cls) * 131 + len(fam) * 17)
    fr = FAMILIES[fam]
    dx = float(rng.uniform(*fr["dx"]))
    dy = float(rng.uniform(*fr["dy"]))
    dz = float(rng.uniform(*fr["dz"]))
    check_admissible(dx, dy, dz)

    stack = CLASS_STACK[cls]
    walls = int(rng.integers(stack["walls"][0], stack["walls"][1] + 1))
    infill_fraction = float(rng.uniform(*stack["infill_range"]))
    porosity = float(rng.uniform(*stack["porosity"]))
    thermal_history_index = float(rng.uniform(0.0, 1.0))
    friction = float(rng.uniform(0.2, 0.6))  # Coulomb-ish prior, ASSUMPTION
    layers = max(1, int(round(dz / LAYER_H_MM)))

    # Solid fraction model: walls occupy perimeter band, infill fills rest.
    wall_band = min(0.9, walls * NOZZLE_MM * 2 * (dx + dy) / (dx * dy + 1e-9))
    solid_fraction = float(min(1.0, max(0.0,
                                        wall_band + (1 - wall_band)
                                        * infill_fraction)))
    rho, rho_status = DENSITIES[material]
    volume_cm3 = dx * dy * dz / 1000.0
    # P-class void-shape correction: strands trap extra air beyond infill.
    void_factor = {"P0": 0.75, "P1": 0.90}.get(cls, 1.0)
    mass_g = volume_cm3 * rho * solid_fraction * void_factor

    strengths = strengths_for_class(cls)
    # Lattice resolution scales with size; capped for sidecar economy.
    nx = max(1, min(12, int(round(dx / 10.0))))
    ny = max(1, min(10, int(round(dy / 10.0))))
    nz = max(1, min(6, layers // max(1, layers // 6)))
    graph: BondGraph = lattice_graph(nx, ny, nz, dx, dy, dz, mass_g,
                                     strengths)
    violations = graph.validate()
    if violations:
        raise RuntimeError(f"bond graph invalid: {violations}")

    oid = f"{cls}-{fam}-{seed:05d}"
    void_desc = (f"{stack['infill']} infill f={infill_fraction:.2f}, "
                 f"{walls} walls x{NOZZLE_MM}mm, {layers} layers x{LAYER_H_MM}mm, "
                 f"porosity~{porosity:.2f}, raster: {stack['raster']}")
    wrap_risk = None
    if cls in ("P0", "P1"):
        strand_len = float(rng.uniform(80.0, 400.0))
        tangle = float(rng.uniform(0.3, 1.0))
        wrap_risk = {"mean_strand_len_mm": round(strand_len, 1),
                     "tangle_index": round(tangle, 3),
                     "metric": round(min(1.0, strand_len / 400.0 * tangle), 3),
                     "note": "wrap-risk heuristic only; NO fracture claim"}
    return {
        "object_id": oid, "seed": seed, "class": cls, "family": fam,
        "dims_mm": {"dx": round(dx, 2), "dy": round(dy, 2),
                    "dz": round(dz, 2)},
        "walls": walls, "wall_thickness_mm": round(walls * NOZZLE_MM, 2),
        "infill": {"kind": stack["infill"],
                   "fraction": round(infill_fraction, 3)},
        "layer": {"height_mm": LAYER_H_MM, "count": layers,
                  "raster": stack["raster"], "nozzle_mm": NOZZLE_MM},
        "porosity": round(porosity, 3),
        "void_structure": void_desc,
        "friction": round(friction, 3),
        "friction_status": "ASSUMPTION",
        "bonds": {"types": ["in_raster", "cross_raster", "inter_layer_z"],
                  "nominal_strengths": strengths,
                  **graph.summary()},
        "thermal_history_index": round(thermal_history_index, 4),
        "thermal_history_note": "UNCERTAINTY param in [0,1]; never crystallinity",
        "material": material, "density_g_cc": rho,
        "density_status": rho_status,
        "volume_cm3": round(volume_cm3, 3),
        "solid_fraction": round(solid_fraction, 3),
        "mass_g": round(mass_g, 3),
        "orientation_quaternion_xyzw": [round(v, 5)
                                        for v in random_quaternion(rng)],
        "flags": CLASS_FLAGS[cls],
        "admissibility": {"box_mm": [MAX_DX, MAX_DY, MAX_DZ],
                          "margin_mm": MARGIN_MM, "result": "PASS"},
        "evidence_level": EVIDENCE,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--class", dest="cls",
                    choices=sorted(CLASS_FAMILIES), required=True)
    ap.add_argument("--family", default=None)
    ap.add_argument("--material", default="PLA", choices=sorted(DENSITIES))
    args = ap.parse_args(argv)
    try:
        meta = generate(args.cls, args.seed, args.family, args.material)
    except OversizeError as exc:
        print(json.dumps({"result": "REJECT", "reason": str(exc),
                          "evidence_level": EVIDENCE}, indent=2))
        return 2
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
