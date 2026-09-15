"""누락/음수 정점 번호와 비정상 좌표가 3MF 검사에서 통과하지 않는다."""
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "release"))
import build_print_release as release

xml = '''<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
<resources><object id="1" type="model"><mesh><vertices>
<vertex x="0" y="0" z="0"/><vertex x="1" y="0" z="0"/>
<vertex x="0" y="1" z="0"/></vertices><triangles>
<triangle v1="0" v2="1" v3="2"/></triangles></mesh></object></resources><build><item objectid="1"/></build></model>'''
with patch.object(release, "model_xml", return_value=xml):
    assert len(release.three_mf_mesh(Path("fixture"))[0]) == 1
for invalid in (xml.replace('v3="2"', ''), xml.replace('v3="2"', 'v3="-1"'),
                xml.replace('v3="2"', 'v3="3"'), xml.replace('x="1"', 'x="nan"'),
                xml.replace('x="1"', 'x="inf"'), xml.replace('millimeter', 'inch'),
                xml.replace('unit="millimeter"', ''), xml.replace('objectid="1"', 'objectid="2"'),
                xml.replace('<item objectid="1"/>', ''),
                xml.replace('</resources>', '<object id="2" type="model"/></resources>')):
    with patch.object(release, "model_xml", return_value=invalid):
        try:
            release.three_mf_mesh(Path("fixture"))
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid 3MF vertex evidence accepted")
print("THREE_MF_VERTEX_UNIT_REFERENCE_EVIDENCE_PASS negative_cases=10")
alias = xml.replace('</resources>', '<object id="2" type="model"><components><component objectid="1"/></components></object></resources>').replace('<item objectid="1"/>', '<item objectid="2"/>')
with patch.object(release, "model_xml", return_value=alias):
    assert len(release.three_mf_mesh(Path("fixture"))[0]) == 1
for invalid in (alias.replace('<component objectid="1"', '<component objectid="2"'),
                alias.replace('<component objectid="1"', '<component transform="1 0 0 0 1 0 0 0 1 5 0 0" objectid="1"')):
    with patch.object(release, "model_xml", return_value=invalid):
        try:
            release.three_mf_mesh(Path("fixture"))
        except ValueError:
            pass
        else:
            raise AssertionError("Unsupported component alias accepted")
mesh = [((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))]
assert release.corresponding_meshes_match(mesh, mesh)
assert not release.corresponding_meshes_match([], [])
assert not release.corresponding_meshes_match(mesh, mesh * 2)
shifted = [tuple(tuple(v + 1 for v in point) for point in face) for face in mesh]
assert not release.corresponding_meshes_match(mesh, shifted)
assert not release.corresponding_meshes_match(mesh, [((float('nan'), 0., 0.), *mesh[0][1:])])
print("THREE_MF_CORRESPONDING_GEOMETRY_PASS")
with patch.object(release, "model_xml", return_value=xml):
    assert release.build_count_and_bounds(Path("fixture")) == (1, True)
for matrix in ("nan 0 0 0 1 0 0 0 1 0 0 0", "1 0 0 0 1 0 0 0 1 inf 0 0",
               "2 0 0 0 1 0 0 0 1 0 0 0", "1 0 0 0 1 0 0 0 1 221 0 0"):
    invalid = xml.replace('<item objectid="1"', '<item transform="' + matrix + '" objectid="1"')
    with patch.object(release, "model_xml", return_value=invalid):
        assert release.build_count_and_bounds(Path("fixture")) == (1, False)
print("THREE_MF_PLATE_TRANSFORM_REJECTION_PASS cases=4")
with tempfile.TemporaryDirectory() as directory:
    source, first, second = [Path(directory) / name for name in ("source.3mf", "first.3mf", "second.3mf")]
    with zipfile.ZipFile(source, "w") as package:
        package.writestr("3D/3dmodel.model", xml)
    release.normalized_3mf(source, first, "fixture")
    release.normalized_3mf(first, second, "fixture")
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as package:
        assert all(item.compress_type == zipfile.ZIP_STORED for item in package.infolist())
    assert release.corresponding_meshes_match(release.three_mf_mesh(source)[0], release.three_mf_mesh(first)[0])
print("THREE_MF_STORED_NORMALIZATION_PASS idempotent=True")
