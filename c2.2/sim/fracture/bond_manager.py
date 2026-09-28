"""I3 fallback bond manager over the I2 BondGraph data model.

Same Cell/Bond/BondGraph types as c2.2/sim/generators/bonds.py, so the
Blast solver can replace this manager later without changing the coupon
harness. Directional failure thresholds derive ONLY from
strengths_for_class nominal orderings scaled by the specimen solid
fraction (geometric area prior) plus small deterministic per-seed scatter.
No invented physics constants; evidence UNCALIBRATED_FRACTURE.

Load model: idealized unit probe along load_dir (unit vector). Per-bond
resolved factor = |dot(bond_axis, load_dir)| (pure geometric projection).
failure_load = threshold / factor (factor 0 -> +inf, never fails).
Fracture = first load level whose removals split the graph (connected
components via surviving bonds). Fragments partition cells exactly, so
mass is conserved by construction; the coupon harness still verifies it.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "generators"))

from bonds import BondGraph, strengths_for_class  # noqa: E402

EVIDENCE = "UNCALIBRATED_FRACTURE"

# Characteristic slip length for the work proxy: S2 radial_gap_mm 0.8
# (design/parameters.json S2 block). Normalization ASSUMPTION for ordering
# only — NOT a measured fracture displacement.
SLIP_MM = 0.8

SCATTER_DEFAULT = 0.02  # deterministic tie-break scatter, ASSUMPTION


class FractureInputError(ValueError):
    """Bad input: invalid graph, bad seed params, bad load direction."""


class NonphysicalError(RuntimeError):
    """Numerically nonphysical state: NaN/non-positive thresholds."""


@dataclass
class Fragment:
    mass_g: float
    com_mm: tuple[float, float, float]
    cells: tuple[int, ...]


@dataclass
class FractureResult:
    peak_load_proxy: float | None  # None == INTACT (no split at any level)
    work_proxy: float
    failed_bond_indices: list[int]
    first_failure_kind: str | None
    fragments: list[Fragment]
    mass_error_g: float
    n_bonds_total: int
    evidence_level: str = EVIDENCE


def _components(ncells: int, surviving: set[int],
                endpoints: list[tuple[int, int]]) -> list[list[int]]:
    parent = list(range(ncells))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in surviving:
        a, b = endpoints[i]
        union(a, b)
    groups: dict[int, list[int]] = {}
    for c in range(ncells):
        groups.setdefault(find(c), []).append(c)
    return list(groups.values())


class BondManager:
    """Deterministic fallback fracture over a BondGraph."""

    def __init__(self, graph: BondGraph, seed: int,
                 solid_fraction: float = 1.0,
                 scatter: float = SCATTER_DEFAULT) -> None:
        problems = graph.validate()
        if problems:
            raise FractureInputError(f"invalid bond graph: {problems}")
        if not (0.0 < solid_fraction <= 1.0):
            raise FractureInputError(
                f"solid_fraction {solid_fraction} not in (0, 1]")
        if not (0.0 <= scatter < 1.0):
            raise FractureInputError(f"scatter {scatter} not in [0, 1)")
        if not isinstance(seed, (int, np.integer)):
            raise FractureInputError(f"seed must be int, got {type(seed)}")
        if int(seed) < 0:
            raise FractureInputError(f"seed {seed} must be >= 0")
        self.graph = graph
        self.seed = int(seed)
        self.solid_fraction = float(solid_fraction)
        self.scatter = float(scatter)
        rng = np.random.default_rng(self.seed)
        self.thresholds: list[float] = []
        for b in graph.bonds:
            jitter = 1.0 + float(rng.uniform(-scatter, scatter))
            thr = b.strength * self.solid_fraction * jitter
            if not math.isfinite(thr) or thr <= 0:
                raise NonphysicalError(
                    f"nonphysical threshold {thr} on bond {b}")
            self.thresholds.append(thr)
        self._centers = {c.id: c.center_mm for c in graph.cells}
        self._endpoints = [(b.a, b.b) for b in graph.bonds]

    def resolve(self, load_dir: tuple[float, ...]) -> list[float]:
        """Per-bond |dot(bond_axis, load_dir)| geometric projection."""
        u = np.asarray(load_dir, dtype=float)
        if u.shape != (3,) or not np.all(np.isfinite(u)):
            raise FractureInputError(f"load_dir must be 3 finite floats")
        n = float(np.linalg.norm(u))
        if n == 0.0:
            raise FractureInputError("load_dir must be nonzero")
        u = u / n
        factors: list[float] = []
        for a, b in self._endpoints:
            d = np.subtract(self._centers[b], self._centers[a])
            dn = float(np.linalg.norm(d))
            if dn == 0.0:
                raise FractureInputError(
                    f"degenerate zero-length bond axis {a}-{b}")
            factors.append(float(abs(np.dot(d / dn, u))))
        return factors

    def failure_loads(self, load_dir: tuple[float, ...]) -> list[float]:
        factors = self.resolve(load_dir)
        out: list[float] = []
        for thr, f in zip(self.thresholds, factors):
            out.append(thr / f if f > 0.0 else math.inf)
        if any(math.isnan(v) for v in out):
            raise NonphysicalError("NaN in failure loads")
        return out

    def run_event(self, load_dir: tuple[float, ...]) -> FractureResult:
        fl = self.failure_loads(load_dir)
        ncells = len(self.graph.cells)
        if not self.graph.bonds or ncells < 2:
            whole = self._fragment(list(range(ncells)))
            return FractureResult(None, 0.0, [], None, [whole], 0.0,
                                  len(self.graph.bonds))
        order = sorted(range(len(fl)), key=lambda i: fl[i])
        if all(v == math.inf for v in fl):
            whole = self._fragment(list(range(ncells)))
            return FractureResult(None, 0.0, [], None, [whole], 0.0,
                                  len(fl))
        first_kind = self.graph.bonds[order[0]].kind
        surviving = set(range(len(fl)))
        failed: list[int] = []
        peak: float | None = None
        i = 0
        while i < len(order):
            level = fl[order[i]]
            if level == math.inf:
                break
            j = i
            while j < len(order) and fl[order[j]] == level:
                surviving.discard(order[j])
                failed.append(order[j])
                j += 1
            i = j
            if len(_components(ncells, surviving, self._endpoints)) > 1:
                peak = level
                break
        if peak is None:  # fully removed yet somehow connected (paranoia)
            peak = min(v for v in fl if v < math.inf)
        comps = _components(ncells, surviving, self._endpoints)
        frags = [self._fragment(c) for c in comps]
        mass_err = abs(sum(f.mass_g for f in frags)
                       - self.graph.object_mass_g)
        work = float(sum(0.5 * fl[k] * SLIP_MM for k in failed))
        if not math.isfinite(work) or (peak is not None
                                       and not math.isfinite(peak)):
            raise NonphysicalError("NaN/non-finite peak or work")
        return FractureResult(peak, work, sorted(failed), first_kind,
                              frags, mass_err, len(fl))

    def components_at_probe(self, load_dir: tuple[float, ...],
                            probe: float) -> list[Fragment]:
        """Fragments after removing bonds with failure_load <= probe."""
        fl = self.failure_loads(load_dir)
        surviving = {i for i, v in enumerate(fl) if v > probe}
        return [self._fragment(c) for c in
                _components(len(self.graph.cells), surviving,
                            self._endpoints)]

    def _fragment(self, cell_ids: list[int]) -> Fragment:
        masses = {c.id: c.mass_g for c in self.graph.cells}
        m = sum(masses[c] for c in cell_ids)
        n = len(cell_ids)
        sx = sum(self._centers[c][0] for c in cell_ids) / n
        sy = sum(self._centers[c][1] for c in cell_ids) / n
        sz = sum(self._centers[c][2] for c in cell_ids) / n
        return Fragment(m, (sx, sy, sz), tuple(sorted(cell_ids)))


def graph_from_meta(meta: dict) -> BondGraph:
    """Rebuild the exact I2 lattice from waste_gen metadata.

    Mirrors c2.2/sim/generators/waste_gen.py lattice sizing (dx/10 capped
    12/10, nz from layer count capped 6). Dims rounded to 0.01 mm can in
    principle flip a round() bin edge; validity never depends on it since
    mass is passed explicitly and re-validated.
    """
    from bonds import lattice_graph  # noqa: E402 (local import: same model)

    d = meta["dims_mm"]
    dx, dy, dz = float(d["dx"]), float(d["dy"]), float(d["dz"])
    layers = int(meta["layer"]["count"])
    nx = max(1, min(12, int(round(dx / 10.0))))
    ny = max(1, min(10, int(round(dy / 10.0))))
    nz = max(1, min(6, layers // max(1, layers // 6)))
    return lattice_graph(nx, ny, nz, dx, dy, dz, float(meta["mass_g"]),
                         strengths_for_class(meta["class"]))
