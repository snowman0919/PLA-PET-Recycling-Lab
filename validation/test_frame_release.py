"""R1 regression: altered cut lists and stale CAD cannot enter P2 nesting."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'validation/physical_v08'),str(ROOT/'analysis/frame_v08')]
import frame_release as frame
import beam_screen

class FrameReleaseTest(unittest.TestCase):
    def test_current_release_is_not_cut_permission(self):
        result=frame.validate(ROOT)
        self.assertEqual(result['members'],40)
        self.assertFalse(result['cut_authorization'])
        self.assertEqual(result['totals']['2020']['length_mm'],15078)
    def test_bending_axial_and_torsion_benchmark(self):
        self.assertEqual(beam_screen.benchmark(),'CANTILEVER_AXIAL_BIAXIAL_BENDING_TORSION_PASS')
    def fixture(self,folder):
        root=Path(folder); todo=[frame.REPORT,frame.CUTLIST,frame.CONTRACT,
             'analysis/frame_v08/results/geometry.json','analysis/frame_v08/results/beam_comparison.json',
             'exports/final/drive_ggm_v08/manifest.json']; seen=set()
        while todo:
            rel=todo.pop()
            if rel in seen:continue
            seen.add(rel);src=ROOT/rel;dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
            if src.suffix=='.json':
                data=json.loads(src.read_text())
                if isinstance(data,dict):
                    for key in ('source_sha256','output_sha256'):
                        if isinstance(data.get(key),dict):todo.extend(data[key])
        return root
    def test_mutations_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'validation') as tmp:
            root=self.fixture(tmp);frame.validate(root)
            for rel in (frame.CUTLIST,frame.CONTRACT,'cad/freecad/drive_v08/assembly.py',
                        'exports/final/drive_ggm_v08/GGM-FULL-ASM.step'):
                with self.subTest(source=rel):
                    path=root/rel; original=path.read_bytes();path.write_bytes(original+b'\nmodified\n')
                    with self.assertRaises(ValueError):frame.validate(root)
                    path.write_bytes(original)
            path=root/frame.REPORT; report=json.loads(path.read_text())
            for mutation in ('permission','member','missing'):
                bad=json.loads(json.dumps(report))
                if mutation=='permission':bad['cut_authorization']=True
                elif mutation=='member':bad['members'][0]['quantity']='2'
                else:bad['members'].pop()
                path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):frame.validate(root)
                path.write_text(json.dumps(report))
    def test_old_cut_list_cannot_enter_nesting(self):
        import profile_nesting
        cuts=profile_nesting.requirements()
        self.assertEqual(len(cuts['2020']),36)
        self.assertEqual(len(cuts['2040']),4)
        self.assertAlmostEqual(sum(x[1] for x in cuts['2020']),15078+36*.5)

if __name__=='__main__': unittest.main()
