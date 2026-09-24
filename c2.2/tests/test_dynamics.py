"""Gate A-F dynamics contract tests (no SimulationApp: manifest/schema only)."""
import glob
import json
import os
import struct

import pytest

C22 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(p):
    with open(p) as f:
        return json.load(f)


def test_full_machine_compound_solids_have_distinct_contact_meshes():
    """A reused STL path erased the south S1 tread in the executable scene."""
    manifest = _load(os.path.join(C22, "sim", "assets", "out", "full",
                                  "bodies.json"))
    solids = manifest["solids"]
    paths = [s["mesh"] for s in solids]
    assert len(paths) == len(set(paths)), "one mesh per STEP solid"
    belts = sorted((s for s in solids if s["name"] == "S1_BELT"),
                   key=lambda s: s["part_bbox"][1])
    assert len(belts) == 2
    for belt in belts:
        path = os.path.join(os.path.dirname(C22), belt["mesh"])
        with open(path, "rb") as handle:
            stl = handle.read()
        n = struct.unpack_from("<I", stl, 80)[0]
        assert len(stl) == 84 + 50 * n
        y = [v[i] for v in struct.iter_unpack("<12fH", stl[84:])
             for i in (4, 7, 10)]
        assert abs(min(y) - belt["part_bbox"][1]) < 0.1
        assert abs(max(y) - belt["part_bbox"][4]) < 0.1
    assert belts[0]["part_bbox"][4] < belts[1]["part_bbox"][1]

def test_usd_manifest_pass():
    m = _load(os.path.join(C22, "sim", "assets", "usd",
                           "machine.sidecar.json"))
    assert m["status"] == "PASS", m["failures"]
    assert m["stage_meters_per_unit"] == 0.001
    assert any(a["prim"] == "/World/F0/Hopper" and a["status"] == "EMITTED"
               for a in m["assets"])
    assert any((a["prim"] or "").startswith("/World/F0/Transfer/")
               for a in m["assets"])


def test_usd_load_pass():
    r = _load(os.path.join(C22, "results", "dyn_usd_load.json"))
    assert r["status"] == "PASS", r["failures"]
    assert r["mesh_count"] >= 8
    assert abs(r["meters_per_unit"] - 0.001) < 1e-9


def test_s1_runs_real_physics():
    files = sorted(glob.glob(os.path.join(C22, "results", "dyn_s1",
                                          "s1_*.summary.json")))
    assert len(files) >= 4, "need W1x2 + W4 + P0 S1 runs"
    for f in files:
        s = _load(f)
        assert s["evidence"] == "REAL_PHYSX_HEADLESS"
        assert s["status"] == "PASS", (f, s["failures"])
        assert s["contact_steps"] > 0
        assert s["bond_breaks"] > 0
        assert s["mass_error_kg"] == 0.0


def test_transfer_derived_only():
    r = _load(os.path.join(C22, "results", "dyn_transfer.json"))
    assert r["status"] == "PASS"
    assert r["c21_mutated"] is False
    assert set(r["derived_assets"]) == {"S1_DISCHARGE", "CHUTE", "S2_ENTRY",
                                        "S2_EXIT"}


def test_screen_proxy_free():
    files = sorted(glob.glob(os.path.join(C22, "results", "dyn_s2",
                                          "s2_*.summary.json")))
    assert len(files) >= 5
    for f in files:
        s = _load(f)
        assert s["evidence"] == "REAL_PHYSX_HEADLESS_HOLE_GEOMETRY"
        assert s["proxy_free"] is True
        assert s["status"] == "PASS", (f, s["failures"])


def test_dt_sweep_complete():
    r = _load(os.path.join(C22, "results", "dyn_dt_sweep.json"))
    assert r["status"] == "PASS", r["failures"]
    assert len(r["rows"]) == 6
    assert {row["dt"] for row in r["rows"]} == {0.0025, 0.005, 0.01}


def test_gap_screen_sweep_complete():
    r = _load(os.path.join(C22, "results", "dyn_gap_screen_sweep.json"))
    assert r["status"] == "PASS", r["failures"]
    assert len(r["s1"]) == 6 and len(r["s2"]) == 12
    for row in r["s1"] + r["s2"]:
        assert row["status"] == "PASS", row


def test_surrogate_refit_additive():
    r = _load(os.path.join(C22, "results", "dyn_surrogate.json"))
    assert r["status"] == "PASS"
    assert r["evidence"] == "REAL_PHYSX_HEADLESS"
    assert r["i6_surrogate_mutated"] is False
    assert r["i5_proxy_deleted"] is False
