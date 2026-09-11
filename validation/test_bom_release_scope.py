"""Check BOM aliases and the documented installation steps."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'release'))
import build_bom_release as bom

class BomReleaseScopeTest(unittest.TestCase):
    def test_retired_motor_alias_is_not_an_order_line(self):
        ids={r['part_id'] for r in bom.expanded_rows()}
        self.assertFalse(ids & bom.GGM_SUPERSEDED_DRIVE)
        self.assertIn('CUT-07',bom.GGM_SUPERSEDED_DRIVE)

    def test_support_parts_map_to_installation_steps(self):
        self.assertEqual(bom.assembly_step_number('CUT-09'),4)
        self.assertEqual(bom.assembly_step_number('CUT-10'),5)
        self.assertEqual(bom.assembly_step_number('CUT-05R'),5)

if __name__=='__main__':unittest.main()
