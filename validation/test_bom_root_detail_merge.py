"""Root declarations and matching fabrication detail describe one part, not two."""
import copy
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from release.build_bom_release import merge_expanded_rows


def row(pid='SP-AX-01',quantity='1'):
    return {'part_id':pid,'quantity':quantity,'notes':'source record',
            'drawing':'part.pdf','critical interface':'8 h6',
            'supplier status':'FABRICATION_HOLD'}


class MergeTest(unittest.TestCase):
    def test_matching_governed_detail_is_not_added_twice(self):
        for pid in ('SP-TG-01','SP-AX-01','SP-AX-02','SP-AW-08'):
            root=[row(pid)];before=copy.deepcopy(root)
            result=merge_expanded_rows(root,[row(pid)])
            self.assertEqual(len(result),1)
            self.assertEqual(result[0]['quantity'],'1')
            self.assertEqual(result[0]['supplier status'],'FABRICATION_HOLD')
            self.assertEqual(root,before)

    def test_unknown_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):
            merge_expanded_rows([row('CUT-05')],[row('CUT-05')])

    def test_quantity_drift_or_invalid_number_is_rejected(self):
        for qty in ('2','0','-1','NaN','Infinity'):
            with self.subTest(qty=qty),self.assertRaises(ValueError):
                merge_expanded_rows([row()],[row(quantity=qty)])

    def test_repeated_detail_is_rejected_even_when_matching(self):
        with self.assertRaises(ValueError):
            merge_expanded_rows([row()],[row(),row()])

    def test_repeated_root_is_rejected(self):
        with self.assertRaises(ValueError): merge_expanded_rows([row(),row()],[])

    def test_new_part_is_added_once(self):
        result=merge_expanded_rows([row()],[row('SP-AX-02')])
        self.assertEqual([r['part_id'] for r in result],['SP-AX-01','SP-AX-02'])


if __name__=='__main__': unittest.main()
