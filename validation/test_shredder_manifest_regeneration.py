"""A fresh metal export must preserve distinct shafts and final support quantities."""
import csv
import hashlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cad.freecad.compact import generate as producer
with tempfile.TemporaryDirectory(prefix="shredder-regen-") as temporary:
    root=Path(temporary)
    with patch.object(producer,"ROOT",root):
        produced=producer.export_metal_parts()
    with (root/"exports/cnc/shredder_manifest.csv").open() as f:
        records=list(csv.DictReader(f))
    by={r["part_id"]:r for r in records}
    assert len(by)==len(records)==len(produced)
    expected={"CUT-05":1,"CUT-05R":1,"CUT-09":4,"CUT-10":4}
    for pid,qty in expected.items():
        row=by[pid]
        assert int(row["quantity"])==qty
        assert row["release_state"]==f"GATE1_QTY_{qty}_ALLOWED_USER_APPROVAL_REQUIRED"
        path=root/f"exports/cnc/{pid}/{pid}.step"
        shape=Part.read(str(path))
        assert shape.isValid() and len(shape.Solids)==1
        note=(path.parent/"drawing_notes.md").read_text()
        assert f"- 수량: {qty}" in note
    left=root/"exports/cnc/CUT-05/CUT-05.step"
    right=root/"exports/cnc/CUT-05R/CUT-05R.step"
    assert hashlib.sha256(left.read_bytes()).digest()!=hashlib.sha256(right.read_bytes()).digest()
print("SHREDDER_SOURCE_REGENERATION_PASS shafts=1+1 sleeves=4 seats=4 physical=NOT_RUN")
