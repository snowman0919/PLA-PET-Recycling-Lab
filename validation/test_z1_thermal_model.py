"""Conservation, source geometry, invalid inputs and Z1/support separation."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analysis.thermal_revision_v08.model import ASSUMPTIONS,network,thermal_screen,refinement_error
from analysis.thermal_revision_v08.compare import configurations


class Z1ThermalTest(unittest.TestCase):
    def setUp(self):
        self.base,self.mount,self.archive,self.configs=configurations()
        self.stations,self.zones=self.configs['combined']

    def simulate(self,**kw):
        return thermal_screen(self.base,self.stations,self.zones,200,0,0,
                              duration=10,**kw)

    def test_reference_and_factors(self):
        self.assertEqual(self.archive['reference_commit'],'e323c54effa956b1b90ba586fdee8f9d89b447d1')
        self.assertEqual(self.configs['reference'][1][0],[45,90])
        self.assertEqual(self.configs['combined'][1][0],[45,85])
        self.assertEqual(self.configs['width_only'][0],self.configs['reference'][0])
        self.assertEqual(self.configs['support_only'][1],self.configs['reference'][1])

    def test_contact_area_and_capacity_scale_with_width(self):
        data=[]
        for name in ('reference','width_only'):
            stations,zones=self.configs[name]
            data.append(network(self.base,stations,zones,200,0,0,.0025,ASSUMPTIONS))
        self.assertAlmostEqual(data[0][-1][0]/data[1][-1][0],45/40)
        self.assertAlmostEqual(data[0][2][-4]/data[1][2][-4],45/40)

    def test_internal_energy_conservation(self):
        r=self.simulate(mode='constant',overrides={'emissivity':0})
        self.assertAlmostEqual(r['heat_input_j'],3600)
        self.assertAlmostEqual(r['stored_heat_j'],3600,places=6)
        self.assertLess(abs(r['global_energy_residual_j']),1e-7)
        self.assertLess(r['max_step_energy_residual_j'],1e-7)
        json.dumps(r,allow_nan=False)

    def test_isothermal_unpowered_equilibrium(self):
        self.base=copy.deepcopy(self.base)
        self.base['heater_zone_power_w']=[0,0,0];self.base['die_heater_power_w']=0
        r=self.simulate()
        self.assertAlmostEqual(r['barrel_peak_c'],ASSUMPTIONS['ambient_c'],places=7)
        self.assertEqual(r['heat_input_j'],0)

    def test_heat_links_are_symmetric_and_conservative(self):
        n=network(self.base,self.stations,self.zones,200,8,.2,.0025,ASSUMPTIONS)
        self.assertTrue(np.allclose(n[3],n[3].T))
        self.assertTrue(np.allclose(n[3].sum(axis=0),0,atol=1e-9))
        self.assertTrue(np.all(n[2]>0))

    def test_support_shift_preserves_total_heat_sink_not_position(self):
        data=[network(self.base,st,z,200,0,.2,.0025,ASSUMPTIONS)
              for st,z in (self.configs['reference'],self.configs['support_only'])]
        self.assertAlmostEqual(sum(data[0][5]),.4)
        self.assertAlmostEqual(sum(data[1][5]),.4)
        self.assertGreater(np.max(abs(data[0][5]-data[1][5])),.01)

    def test_invalid_inputs(self):
        for overrides in ({'steel_cp_j_kg_k':0},{'steel_k_w_m_k':float('nan')},
                          {'emissivity':2},{'heater_capacity_j_k':-1}):
            with self.subTest(overrides=overrides),self.assertRaises(ValueError):
                self.simulate(overrides=overrides)
        for dt in (0,-1,float('nan'),3):
            with self.subTest(dt=dt),self.assertRaises(ValueError): self.simulate(dt=dt)

    def test_overlapping_zones_rejected(self):
        zones=copy.deepcopy(self.zones);zones[0][1]=zones[1][0]+1
        with self.assertRaises(ValueError):
            thermal_screen(self.base,self.stations,zones,200,8,.2,duration=10)

    def test_refinement_checks_heater_and_sensor_not_only_barrel(self):
        r=self.simulate(); corrupt=copy.deepcopy(r)
        corrupt['heater_peaks_c'][0]+=5
        self.assertAlmostEqual(refinement_error(r,corrupt),5)
        self.assertFalse(r['fabrication_authorized'])


if __name__=='__main__': unittest.main()
