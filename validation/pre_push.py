"""C1 compatibility gate for the existing repository pre-push hook."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
R=Path(__file__).resolve().parents[1]
python=R/'.venv/bin/python'
subprocess.run([str(python) if python.exists() else sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=R,check=True)
manifest=json.loads((R/'results/artifact_sha256.json').read_text())
for name,digest in manifest.items():
    assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,'Stale artifact: '+name
state=json.loads((R/'results/release_state.json').read_text())
assert all(state[x]=='HOLD' for x in ['procurement','fabrication','energization'])
roundtrip=json.loads((R/'results/step_roundtrip.json').read_text())
assert roundtrip['passed'] and roundtrip['part_count']==115 and roundtrip['assembly_solids']==199
assert all(x['passed'] for x in roundtrip['parts'])
native=json.loads((R/'results/freecad_build.json').read_text())
assert len(native['parts'])==115 and native['objects']==199
assert all(x['valid'] and x['solids']==1 for x in native['parts'])
assert max(x['relative_volume_difference'] for x in native['parity'])<1e-5
engineering=json.loads((R/'results/engineering.json').read_text())
assert engineering['power_allocator_exhaustive']['passed']
assert engineering['power']['psu_nameplate_W']==800
assert engineering['power']['psu_current_A']==33
assert engineering['power']['operational_cap_W']==500
assert engineering['power']['psu_current_derived_ceiling_W']==792
assert json.loads((R/'results/cad_intersections.json').read_text())['contacts']==[]
print('C1 digital pre-push gate passed. Procurement, fabrication and energization remain HOLD.')
