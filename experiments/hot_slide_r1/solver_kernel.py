"""Scoped MIT solver adapters copied from PPR; source provenance in manifest."""
import os,math,re,subprocess,shutil
from pathlib import Path

def parse_frd(path: Path) -> dict:
    mode = ""
    max_displacement = 0.0
    max_vm = 0.0
    max_vm_node = None
    records = {"DISP": 0, "STRESS": 0}
    number_pattern = re.compile(r"[-+]?\d*\.?\d+(?:E[-+]?\d+)?")
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith(" -4"):
            mode = "DISP" if "DISP" in line else "STRESS" if "STRESS" in line else ""
            continue
        if line.startswith(" -3"):
            mode = ""
            continue
        if not mode or not line.startswith(" -1"):
            continue
        record = [float(value) for value in number_pattern.findall(line)]
        values = record[2:]
        expected = 3 if mode == "DISP" else 6
        if len(record) != expected + 2 or not all(math.isfinite(value) for value in record):
            raise ValueError(f"invalid {mode} FRD record in {path}")
        records[mode] += 1
        if mode == "DISP" and len(values) >= 3:
            max_displacement = max(max_displacement, math.sqrt(sum(value**2 for value in values[:3])))
        if mode == "STRESS" and len(values) >= 6:
            sx, sy, sz, txy, tyz, tzx = values[:6]
            vm = math.sqrt(0.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2)+3*(txy**2+tyz**2+tzx**2))
            if max_vm_node is None or vm > max_vm:
                max_vm, max_vm_node = vm, int(record[1])
    if mode:
        raise ValueError(f"FRD result block not terminated: {path}")
    if not all(records.values()):
        raise ValueError(f"FRD missing displacement/stress data: {path}: {records}")
    return {"max_displacement_mm": max_displacement * 1000, "max_von_mises_mpa": max_vm / 1e6,
            "max_von_mises_node_id": max_vm_node}

def run(command: list[str], cwd: Path, log: Path, env: dict[str, str] | None = None, input_text: str | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=env, input=input_text, timeout=300)
    output = result.stdout + result.stderr
    log.write_text(output)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{output[-2000:]}")
    return output

def nset(name: str, nodes: list[int]) -> list[str]:
    if not nodes:
        raise RuntimeError(f"empty node set {name}")
    return [f"*NSET,NSET={name}"] + [",".join(map(str, nodes[index:index+16])) for index in range(0, len(nodes), 16)]

def reactions(path: Path, selected: set[int], coordinates_m: dict[int, tuple[float, float, float]]) -> dict:
    mode = False
    forces: dict[int, tuple[float, float, float]] = {}
    pattern = re.compile(r"[-+]?\d*\.?\d+(?:E[-+]?\d+)?")
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith(" -4"):
            mode = "FORC" in line
            continue
        if line.startswith(" -3"):
            mode = False
        if not mode or not line.startswith(" -1"):
            continue
        values = pattern.findall(line)
        node = int(values[1])
        if node in selected:
            forces[node] = tuple(float(value) for value in values[2:5])
    total = [sum(force[axis] for force in forces.values()) for axis in range(3)]
    moment = [0.0, 0.0, 0.0]
    for node, force in forces.items():
        x, y, z = coordinates_m[node]
        fx, fy, fz = force
        moment[0] += y*fz - z*fy
        moment[1] += z*fx - x*fz
        moment[2] += x*fy - y*fx
    return {"node_count": len(forces), "force_n": total, "moment_about_origin_nm": moment}

def solve(case_dir: Path, deck: str, reaction_selection: tuple[set[int], dict[int, tuple[float, float, float]]] | None = None) -> dict:
    (case_dir / "model.inp").write_text(deck)
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    output = run([shutil.which("ccx") or "ccx", "model"], case_dir, case_dir / "ccx.log", env)
    frd = case_dir / "model.frd"
    if not frd.exists() or "JOB FINISHED" not in output.upper():
        raise RuntimeError(f"{case_dir.name}: CalculiX did not finish")
    parsed = parse_frd(frd)
    parsed.update({"status": "PASS", "omp_num_threads": 1, "negative_jacobian": "negative jacobian" in output.lower()})
    if reaction_selection:
        parsed["reaction"] = reactions(frd, *reaction_selection)
    if parsed["negative_jacobian"]:
        raise RuntimeError(f"{case_dir.name}: negative Jacobian")
    return parsed
