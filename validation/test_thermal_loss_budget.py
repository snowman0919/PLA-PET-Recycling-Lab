"""Loss-budget diagnostics may not pretend to qualify insulation or power upgrades."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analysis.thermal_revision_v08.loss_budget import loss_case
from analysis.thermal_revision_v08.steady_state import required_power

class LossBudgetTests(unittest.TestCase):
    def setUp(self):
        self.base=json.loads((ROOT/'cad/parameters/baseline.json').read_text())['extruder']
        self.zones=self.base['heater_zone_axial_ranges_from_barrel_rear_mm']

    def test_unit_factor_reproduces_current_inverse_solver(self):
        actual=loss_case(self.base,[.016,.110],self.zones,1.,200.,15.,.2)
        expected=required_power(self.base,[.016,.110],self.zones,contact=200.,air=15.,support=.2)
        for a,b in zip(actual['required_watts'],expected['required_watts']):
            self.assertAlmostEqual(a,b,places=8)
        self.assertFalse(actual['heating_only_feasible'])
        self.assertFalse(actual['hardware_solution_defined'])
        self.assertFalse(actual['supplier_rating_verified'])

    def test_bad_multiplier_rejected(self):
        for factor in (0,-1,1.1,float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):
                loss_case(self.base,[.016,.110],self.zones,factor,200.,15.,.2)

    def test_power_feasibility_does_not_hide_hot_sheath(self):
        row=loss_case(self.base,[.016,.110],self.zones,.25,200.,15.,.2)
        self.assertTrue(row['heating_only_feasible'])
        self.assertTrue(row['heater_comparison_exceeded'])
        self.assertEqual(row['contact_w_m2k'],200.)
        self.assertEqual(row['support_w_k'],.2)
        self.assertEqual(row['rated_watts'],[100.,100.,100.,60.])
        self.assertEqual(row['physical_validation_state'],'NOT_RUN')
        self.assertFalse(row['energization_authorized'])

if __name__=='__main__': unittest.main()
