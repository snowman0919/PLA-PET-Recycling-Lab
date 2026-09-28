"""I2 bond-graph: cells/chunks + directional bonds (nominal strengths only).

Evidence: UNCALIBRATED_DIGITAL_SENSITIVITY. Nominal strengths are ordering
priors for architecture search, NEVER calibrated fracture thresholds.
"""
from __future__ import annotations

from dataclasses import dataclass, field

BOND_TYPES = ("in_raster", "cross_raster", "inter_layer_z")

# Per-class nominal strengths (dimensionless, in_raster normalized to 1.0).
# W1 Z-weakest; W4 near-isotropic. UNCERTAINTY priors, not measurements.
CLASS_STRENGTHS: dict[str, dict[str, float]] = {
    "W1": {"in_raster": 1.00, "cross_raster": 0.55, "inter_layer_z": 0.25},
    "W2": {"in_raster": 1.00, "cross_raster": 0.80, "inter_layer_z": 0.60},
    "W3": {"in_raster": 1.00, "cross_raster": 0.85, "inter_layer_z": 0.70},
    "W4": {"in_raster": 1.00, "cross_raster": 0.97, "inter_layer_z": 0.95},
    "P0": {"in_raster": 0.60, "cross_raster": 0.40, "inter_layer_z": 0.15},
    "P1": {"in_raster": 0.90, "cross_raster": 0.80, "inter_layer_z": 0.70},
    "P2": {"in_raster": 1.00, "cross_raster": 0.98, "inter_layer_z": 0.96},
}


class MissingEvidenceError(RuntimeError):
    """Raised when calibrated (measured) strength data is requested.

    No physical shredding tests exist (BLOCKED_PERFORMANCE_DATA); only
    nominal UNCALIBRATED_DIGITAL_SENSITIVITY orderings are available.
    """


def strengths_for_class(cls: str) -> dict[str, float]:
    try:
        return dict(CLASS_STRENGTHS[cls])
    except KeyError:
        raise ValueError(f"unknown waste class {cls!r}") from None


def require_calibrated_strength(cls: str) -> float:
    """Calibrated fracture strength lookup — always fails loudly (no data)."""
    raise MissingEvidenceError(
        f"no calibrated strength data for class {cls!r}; "
        "performance gate BLOCKED_PERFORMANCE_DATA, zero physical tests")


@dataclass
class Cell:
    id: int
    mass_g: float
    center_mm: tuple[float, float, float]


@dataclass
class Bond:
    a: int
    b: int
    kind: str
    strength: float  # nominal, dimensionless; see module docstring


@dataclass
class BondGraph:
    object_mass_g: float
    cells: list[Cell] = field(default_factory=list)
    bonds: list[Bond] = field(default_factory=list)
    evidence_level: str = "UNCALIBRATED_DIGITAL_SENSITIVITY"

    def validate(self, tol_g: float = 1e-6) -> list[str]:
        """Return list of violations (empty == valid)."""
        problems: list[str] = []
        ids = {c.id for c in self.cells}
        if len(ids) != len(self.cells):
            problems.append("duplicate cell ids")
        total = sum(c.mass_g for c in self.cells)
        if abs(total - self.object_mass_g) > tol_g:
            problems.append(
                f"mass conservation violated: sum(cells)={total:.6f}g "
                f"!= object {self.object_mass_g:.6f}g")
        for i, b in enumerate(self.bonds):
            if b.a == b.b:
                problems.append(f"bond {i}: self-bond on cell {b.a}")
            if b.a not in ids or b.b not in ids:
                problems.append(f"bond {i}: dangling endpoint {b.a}-{b.b}")
            if b.kind not in BOND_TYPES:
                problems.append(f"bond {i}: unknown kind {b.kind!r}")
            if not b.strength > 0:
                problems.append(f"bond {i}: non-positive strength {b.strength}")
        for c in self.cells:
            if not c.mass_g > 0:
                problems.append(f"cell {c.id}: non-positive mass")
        return problems

    @property
    def is_valid(self) -> bool:
        return not self.validate()

    def summary(self) -> dict:
        counts = {k: 0 for k in BOND_TYPES}
        for b in self.bonds:
            if b.kind in counts:
                counts[b.kind] += 1
        return {"cells": len(self.cells), "bonds": len(self.bonds),
                "bonds_by_type": counts, "valid": self.is_valid}


def lattice_graph(nx: int, ny: int, nz: int, dx: float, dy: float, dz: float,
                  mass_g: float, strengths: dict[str, float]) -> BondGraph:
    """6-neighbourhood lattice; x->in_raster, y->cross_raster, z->inter_layer_z.

    Cell mass uniform (mass / N). Deterministic ordering (z,y,x loops).
    """
    if min(nx, ny, nz) < 1:
        raise ValueError("lattice dims must be >= 1")
    cells = [Cell(id=k, mass_g=mass_g / (nx * ny * nz),
                  center_mm=((i + 0.5) * dx / nx, (j + 0.5) * dy / ny,
                             (k_ + 0.5) * dz / nz))
             for k_ in range(nz) for j in range(ny) for i in range(nx)
             for k in [k_ * ny * nx + j * nx + i]]
    idx = lambda i, j, k_: k_ * ny * nx + j * nx + i  # noqa: E731
    bonds: list[Bond] = []
    for k_ in range(nz):
        for j in range(ny):
            for i in range(nx):
                if i + 1 < nx:
                    bonds.append(Bond(idx(i, j, k_), idx(i + 1, j, k_),
                                      "in_raster", strengths["in_raster"]))
                if j + 1 < ny:
                    bonds.append(Bond(idx(i, j, k_), idx(i, j + 1, k_),
                                      "cross_raster", strengths["cross_raster"]))
                if k_ + 1 < nz:
                    bonds.append(Bond(idx(i, j, k_), idx(i, j, k_ + 1),
                                      "inter_layer_z",
                                      strengths["inter_layer_z"]))
    return BondGraph(object_mass_g=mass_g, cells=cells, bonds=bonds)
