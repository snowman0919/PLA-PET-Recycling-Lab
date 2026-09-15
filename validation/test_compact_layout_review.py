"""Real CAD regressions for space reuse; no manufacturing authorization."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'cad/freecad/drive_v08')]
from analysis.compact_layout_v08 import review as r
from cad.freecad.final_v08.generate import final_objects
from cad.freecad.drive_v08.assembly import integrated_objects

class CompactLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads(r.CONTRACT.read_text())
        cls.base,_=integrated_objects(final_objects())
        cls.proposed,cls.transforms=r.placement(cls.base)

    def copy(self):
        return [dict(row,shape=row['shape'].copy()) for row in self.proposed]

    def test_envelope_and_shape_preservation(self):
        self.assertEqual(r.check_preserved(self.base,self.proposed,self.transforms),len(self.base))
        for actual,target in zip(r.dimensions(self.proposed),(470,700,930)):
            self.assertAlmostEqual(actual,target,places=5)
        self.assertEqual(len(r.check_supports(self.base,self.proposed)),8)

    def test_missing_motor_rejected(self):
        bad=[row for row in self.proposed if row['name']!='GGM_Shredder']
        with self.assertRaisesRegex(ValueError,'omission'):
            r.check_preserved(self.base,bad,self.transforms)

    def test_floating_rail_rejected(self):
        bad=self.copy(); r.by_name(bad)['GGM_ShredRail'].translate(App.Vector(0,0,0.1))
        with self.assertRaisesRegex(ValueError,'lost support'):
            r.check_supports(self.base,bad)

    def test_collector_offset_rejected(self):
        bad=self.copy(); r.by_name(bad)['FlakeBin'].translate(App.Vector(100,0,0))
        with self.assertRaisesRegex(ValueError,'collector'):
            r.check_collection(bad)

    def test_lid_lift_rejected(self):
        bad=self.copy(); r.by_name(bad)['PPR-C01_SlidingLid'].translate(App.Vector(0,0,2))
        with self.assertRaisesRegex(ValueError,'cover'):
            r.check_lid(bad,self.spec)

    def test_service_obstruction_rejected(self):
        bad=self.copy(); b=r.by_name(bad)['PPR-C01_SlidingLid'].BoundBox
        bad.append(dict(name='ServiceBlock',shape=Part.makeBox(5,5,5,App.Vector(b.XMin-10,b.YMin+5,b.ZMin))))
        with self.assertRaisesRegex(ValueError,'obstructed'):
            r.check_lid(bad,self.spec)

    def test_simple_inset_is_not_accepted(self):
        bad,_=r.placement(self.base,(0,10,0),(0,10,0)); by=r.by_name(bad)
        self.assertGreater(by['SealedFeedHopper'].common(by['GGM_SH_Post_238_313']).Volume,1000)

    def test_positive_lid_and_collector(self):
        self.assertTrue(r.check_lid(self.proposed,self.spec)['closed_mouth_covered'])
        self.assertGreaterEqual(min(r.check_collection(self.proposed)['inward_margins_mm']),4.999999)

    def test_step_internal_geometry_not_just_volume(self):
        stock=Part.makeBox(20,20,20); left=stock.copy(); right=stock.copy()
        for x,y in ((5,10),(15,10)):
            left=left.cut(Part.makeCylinder(1,20,App.Vector(x,y,0)))
        for x,y in ((10,5),(10,15)):
            right=right.cut(Part.makeCylinder(1,20,App.Vector(x,y,0)))
        self.assertAlmostEqual(left.Volume,right.Volume,places=5)
        self.assertLess((left.Solids[0].CenterOfMass-right.Solids[0].CenterOfMass).Length,1e-5)
        with self.assertRaisesRegex(ValueError,'geometry differs'):
            r.compare_solids(left.Solids,right.Solids)
        result=r.compare_solids(left.Solids,left.copy().Solids)
        self.assertLess(result['missing_total_mm3'],0.01)

if __name__=='__main__': unittest.main()
