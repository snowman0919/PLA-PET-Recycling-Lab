#!/usr/bin/env python3
"""유지판 유한 지지 모델 준비: SPRING2 요소 검증, 실제 볼트 강성 인증 아님."""
import hashlib
import argparse
import json
import math
import tempfile
from pathlib import Path
import run_qualification_v08 as qualification
from run_calculix_v08 import read_gmsh_inp, nset, solve


def verify_sources(report, root, seen=None):
    """Check recorded dependencies through intermediate JSON evidence."""
    seen = set() if seen is None else seen
    for path, digest in report["source_sha256"].items():
        source = root / path
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, path
        if source.suffix == ".json" and source not in seen:
            seen.add(source)
            nested = json.loads(source.read_text())
            if isinstance(nested, dict) and "source_sha256" in nested:
                verify_sources(nested, root, seen)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh", type=float, choices=(.5,.7), default=.5)
    mesh = parser.parse_args().mesh
    filename = "retainer_support_sensitivity.json" if mesh == .5 else "retainer_support_sensitivity_0.7.json"
    output = qualification.OUT.parent / filename
    output.write_text(json.dumps({"status": "INCOMPLETE", "physical_validation_state": "NOT_RUN"})+"\n")
    reference_path = qualification.OUT.parent / "retainer_candidate_fea.json"
    reference = json.loads(reference_path.read_text())
    verify_sources(reference, qualification.ROOT)
    qualification.RAW = Path(tempfile.mkdtemp(prefix="support-spring-", dir=qualification.OUT.parent))
    rows = []
    for stiffness in (1e4, 1e5, 1e6):  # N/mm, illustrative stiffness sweep only.
        force = 620.
        deck = f"""*HEADING
SPRING2 unit check; SI
*NODE,NSET=ALL
1,0.,0.,0.
2,0.001,0.,0.
*ELEMENT,TYPE=SPRING2,ELSET=SUPPORT
1,1,2
*SPRING,ELSET=SUPPORT
1,1
{stiffness*1000:.1f}
*BOUNDARY
1,1,3,0.
2,2,3,0.
*STEP
*STATIC
*CLOAD
2,1,{force}
*NODE PRINT,NSET=ALL
U,RF
*END STEP
"""
        case, data = qualification.run(f"k{stiffness:g}", deck)
        displacement = qualification.numbers_after(data, "displacements")
        reaction = qualification.numbers_after(data, "forces")
        u = next(r[1] for r in displacement if r[0] == 2)
        rf = next(r[1] for r in reaction if r[0] == 1)
        assert math.isclose(u*1000, force/stiffness, rel_tol=1e-5)
        assert math.isclose(rf, -force, rel_tol=1e-5)
        rows.append({"stiffness_n_mm": stiffness, "load_n": force, "displacement_mm": u*1000,
                     "anchor_reaction_n": rf, "deck_sha256": hashlib.sha256((case/"model.inp").read_bytes()).hexdigest()})
    reference_mesh = next(row for row in reference["meshes"] if row["mesh_mm"] == mesh)
    original = qualification.ROOT / reference["raw_directory"] / f"mesh_{mesh}/model.inp"
    assert hashlib.sha256(original.read_bytes()).hexdigest() == reference_mesh["deck_sha256"]
    base = original.read_text()
    nodes, elements = read_gmsh_inp(original)  # This frozen deck is already in SI.
    groups = [{n for n, (x,y,z) in nodes.items() if abs(math.hypot(y-cy,z-.382)-.00165)<1e-8}
              for cy in (.318,.376)]
    assert all(groups) and not groups[0] & groups[1]
    fixed = set.union(*groups)
    assert len(fixed) == reference_mesh["result"]["reaction"]["node_count"]
    coupled = []
    for stiffness in (1e4,1e5,1e6):
        coordinates = dict(nodes)
        cards, anchors = ["*NODE"], []
        spring_cards = []
        eid = max(int(e.split(",")[0]) for e in elements)
        for index, group in enumerate(groups):
            spring_cards.append(f"*ELEMENT,TYPE=SPRING2,ELSET=SUPPORT{index}")
            for node in sorted(group):
                anchor = max(coordinates)+1
                x,y,z = nodes[node]
                coordinates[anchor] = (x-.001,y,z)
                anchors.append(anchor)
                cards.append(f"{anchor},{x-.001},{y},{z}")
                eid += 1
                spring_cards.append(f"{eid},{node},{anchor}")
            spring_cards += [f"*SPRING,ELSET=SUPPORT{index}", "1,1", f"{stiffness*1000/len(group):.12f}"]
        cards += spring_cards + nset("ANCHORS", anchors)
        needle = "*BOUNDARY\nFIXED,1,3,0"
        assert base.count(needle) == 1
        deck = base.replace(needle, "\n".join(cards)+"\n*BOUNDARY\nFIXED,2,3,0\nANCHORS,1,3,0")
        case = qualification.RAW / f"plate_k{stiffness:g}"
        case.mkdir()
        response = solve(case, deck, (fixed | set(anchors), coordinates))
        assert response["reaction"]["node_count"] == len(fixed)+len(anchors)
        assert abs(response["reaction"]["force_n"][0]+reference["thrust_n"]) < .01
        reference_reaction = reference_mesh["result"]["reaction"]
        force_delta = [a-b for a,b in zip(response["reaction"]["force_n"], reference_reaction["force_n"])]
        moment_delta = [a-b for a,b in zip(response["reaction"]["moment_about_origin_nm"], reference_reaction["moment_about_origin_nm"])]
        assert max(map(abs, force_delta)) < .01
        assert max(map(abs, moment_delta)) < .01
        coupled.append({"per_bore_stiffness_n_mm": stiffness, "result": response,
                        "force_delta_from_fixed_reference_n": force_delta,
                        "moment_delta_from_fixed_reference_nm": moment_delta,
                        "deck_sha256": hashlib.sha256((case/"model.inp").read_bytes()).hexdigest()})
    assert all(a["result"]["max_displacement_mm"] > b["result"]["max_displacement_mm"] for a,b in zip(coupled,coupled[1:]))
    result = {"status": "HOLD", "element_benchmark": "PASS", "cases": rows,
              "mesh_mm": mesh,
              "retainer_fixed_mesh_sensitivity": coupled,
              "reference_deck_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
              "raw_directory": str(qualification.RAW.relative_to(qualification.ROOT)),
              "source_sha256": {str(p.relative_to(qualification.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (Path(__file__).resolve(), Path(qualification.__file__).resolve(),
                                          qualification.ROOT/"analysis/final_validation/run_calculix_v08.py",
                                          qualification.ROOT/"analysis/structural/run_load_checks.py",
                                          reference_path, original)},
              "scope": "Frozen reference retainer mesh, equal nodal axial springs normalized per bore; transverse DOFs fixed. Distribution is mesh-dependent, not a contact/bolt model. Illustrative stiffnesses, not measured joint data. Physical validation NOT_RUN."}
    output.write_text(json.dumps(result, indent=2)+"\n")
    print("SUPPORT_SPRING_BENCHMARK_PASS cases=3 assembly=HOLD")


if __name__ == "__main__":
    main()
