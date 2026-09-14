"""Reject obsolete launch counts, omitted frame inputs and altered bound bytes."""
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from build_physical_launch_package import SOURCE_BINDINGS
from validate_physical_launch_package import validate_source_binding_payload


class LaunchBindingTest(unittest.TestCase):
    def setUp(self):
        temporary = ROOT / '.build' / 'launch-binding-tests'
        temporary.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=temporary)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.contents = {}
        for source in SOURCE_BINDINGS:
            p = self.root / source
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(('fixture:' + source).encode())
            self.contents['07_SOURCE_BINDINGS/' + source] = p.read_bytes()
        self.status = {'source_binding_count': len(SOURCE_BINDINGS)}

    def validate(self, contents=None, status=None):
        contents = self.contents if contents is None else contents
        status = self.status if status is None else status
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as out:
            for name, data in contents.items():
                out.writestr(name, data)
        buffer.seek(0)
        with zipfile.ZipFile(buffer) as archive:
            return validate_source_binding_payload(archive, set(archive.namelist()), status, self.root)

    def test_current_sixteen_inputs(self):
        self.assertEqual(len(SOURCE_BINDINGS), 16)
        self.assertTrue({'cad/parameters/ggm_frame_revision.json',
            'exports/fabrication/frame_cut_list.csv',
            'exports/final/frame_v08/frame_release.json',
            'exports/final/frame_v08/FRAME_CUT_AND_TIE_KO.pdf'} <= set(SOURCE_BINDINGS))
        self.validate()

    def test_old_count_rejected(self):
        with self.assertRaisesRegex(SystemExit, 'count drift'):
            self.validate(status={'source_binding_count': 12})

    def test_noninteger_count_rejected(self):
        for value in ('16', 16.0, True, None):
            with self.subTest(value=value), self.assertRaisesRegex(SystemExit, 'count drift'):
                self.validate(status={'source_binding_count': value})

    def test_missing_frame_binding(self):
        data = dict(self.contents)
        data.pop('07_SOURCE_BINDINGS/exports/fabrication/frame_cut_list.csv')
        with self.assertRaisesRegex(SystemExit, 'coverage drift'):
            self.validate(contents=data)

    def test_unexpected_binding(self):
        data = dict(self.contents)
        data['07_SOURCE_BINDINGS/unexpected.json'] = b'{}'
        with self.assertRaisesRegex(SystemExit, 'coverage drift'):
            self.validate(contents=data)

    def test_tampered_frame_content(self):
        data = dict(self.contents)
        data['07_SOURCE_BINDINGS/exports/fabrication/frame_cut_list.csv'] = b'wrong cuts'
        with self.assertRaisesRegex(SystemExit, 'content drift'):
            self.validate(contents=data)

    def test_missing_local_source(self):
        (self.root / SOURCE_BINDINGS[0]).unlink()
        with self.assertRaisesRegex(SystemExit, 'content drift'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
