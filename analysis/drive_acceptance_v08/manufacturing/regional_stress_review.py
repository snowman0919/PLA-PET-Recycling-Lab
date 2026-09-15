"""Converged non-singular thrust-plate web stress review.

Uses existing C3D10 result files. It deliberately excludes the loaded 51102
seat and rigid bolt-bore idealizations before evaluating design stress.
"""
from pathlib import Path
import hashlib, json, math, re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = HERE / "raw" / "plate_quadratic"
PATTERN = re.compile(r"[-+]?\d*\.?\d+(?:E[-+]?\d+)?")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_nodes(path: Path):
    nodes, section = {}, ""
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line.startswith("*"):
            section = "NODE" if line.upper() == "*NODE" else ""
            continue
        if section and line:
            cols = [item.strip() for item in line.split(",")]
            nodes[int(cols[0])] = tuple(map(float, cols[1:4]))
    if not nodes:
        raise RuntimeError("mesh nodes missing")
    return nodes


def read_von_mises(path: Path):
    stress, active = {}, False
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith(" -4"):
            active = "STRESS" in line
            continue
        if line.startswith(" -3"):
            active = False
            continue
        if not active or not line.startswith(" -1"):
            continue
        values = PATTERN.findall(line)
        if len(values) < 8:
            continue
        node = int(values[1])
        sx, sy, sz, sxy, syz, szx = map(float, values[2:8])
        vm = math.sqrt(
            0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2)
            + 3.0 * (sxy * sxy + syz * syz + szx * szx)
        )
        stress[node] = vm
    if not stress:
        raise RuntimeError("FRD stress block missing")
    return stress


def in_web(x: float, _y: float, z: float) -> bool:
    # Bearing centre is X320/Z382.  The loaded seat ends below R14.2 mm.
    # X/Z box stays away from the four rigid bolt-bore idealizations.
    radius = math.hypot(x - 320.0, z - 382.0)
    return 295.0 < x < 345.0 and 350.0 < z < 414.0 and radius > 16.0


def percentile(values, fraction):
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((len(ordered) - 1) * fraction))
    return ordered[index]


def summarize(case: str):
    folder = RAW / case
    nodes = read_nodes(folder / "gmsh.inp")
    stress = read_von_mises(folder / "model.frd")
    values = [stress[node] for node, xyz in nodes.items()
              if node in stress and in_web(*xyz)]
    if len(values) < 500:
        raise RuntimeError(f"regional probe too sparse: {case}")
    return {
        "case": case,
        "node_count": len(values),
        "max_mpa": max(values),
        "p99_mpa": percentile(values, 0.99),
        "p95_mpa": percentile(values, 0.95),
        "p90_mpa": percentile(values, 0.90),
        "mean_mpa": sum(values) / len(values),
        "mesh_sha256": sha(folder / "gmsh.inp"),
        "frd_sha256": sha(folder / "model.frd"),
    }


def main():
    rows = [summarize(f"r2_{size}") for size in ("4.0", "3.0", "2.0")]
    medium, fine = rows[-2:]
    delta = lambda key: abs(medium[key] / fine[key] - 1.0)
    convergence = {
        "regional_max_fraction": delta("max_mpa"),
        "regional_p99_fraction": delta("p99_mpa"),
        "regional_p95_fraction": delta("p95_mpa"),
        "regional_p90_fraction": delta("p90_mpa"),
    }
    convergence_pass = (
        convergence["regional_max_fraction"] <= 0.05
        and convergence["regional_p95_fraction"] <= 0.05
        and convergence["regional_p99_fraction"] <= 0.10
    )
    yield_reference_mpa = 275.0
    result = {
        "status": "REGIONAL_STRESS_CONVERGED" if convergence_pass else "REVIEW_REQUIRED",
        "physical_validation": "NOT_RUN",
        "machine_release": "HOLD",
        "probe_definition": {
            "x_mm": [295.0, 345.0],
            "z_mm": [350.0, 414.0],
            "bearing_centre_xz_mm": [320.0, 382.0],
            "excluded_radius_mm": 16.0,
            "reason": "exclude loaded bearing seat and rigid bolt-bore singularities; retain the load-path web",
        },
        "cases": rows,
        "medium_to_fine": convergence,
        "convergence_pass": convergence_pass,
        "fine_regional_max_mpa": fine["max_mpa"],
        "fine_regional_p95_mpa": fine["p95_mpa"],
        "yield_reference_mpa": yield_reference_mpa,
        "regional_max_yield_screen_sf": yield_reference_mpa / fine["max_mpa"],
        "limits": [
            "Cold linear-elastic local plate model only",
            "Yield reference is a screening value, not material certificate evidence",
            "Nodal peak at rigid constraints remains diagnostic and is not reclassified as converged",
        ],
        "source_sha256": {
            str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
            "analysis/drive_acceptance_v08/manufacturing/retention_strength_quadratic.json":
                sha(HERE / "retention_strength_quadratic.json"),
        },
    }
    (HERE / "regional_stress.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not convergence_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
