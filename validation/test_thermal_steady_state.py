"""Independent linear-network solution and physical inverse-demand checks."""
import copy
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analysis.thermal_revision_v08 import steady_state as model
from analysis.thermal_revision_v08.compare import configurations


class SteadyHeatTest(unittest.TestCase):
    def setUp(self):
        self.base, _, _, configs = configurations()
        self.stations, self.zones = configs['combined']

    def test_independent_linear_star_solution(self):
        links = np.array([1.,2.,3.,4.]); losses = np.array([.5,.2,.3,.4,.5])
        g = np.zeros((5,5))
        for i,k in enumerate(links,1):
            g[0,0]+=k; g[i,i]+=k; g[0,i]-=k; g[i,0]-=k
        sensors = np.c_[np.zeros(4), np.eye(4)]
        fixture = (np.array([.1]),np.array([.2]),np.ones(5),g,np.zeros(5),
                   losses,sensors,[.1]*3)
        targets = np.asarray(self.base['pet_zone_c']+[self.base['pet_die_c']])
        barrel = (links@targets+losses[0]*25)/(sum(links)+losses[0])
        expected = links*(targets-barrel)+losses[1:]*(targets-25)
        with patch.object(model,'network',return_value=fixture):
            result = model.required_power(self.base,self.stations,self.zones,
                                           overrides={'emissivity':0})
        np.testing.assert_allclose(result['required_watts'],expected,atol=1e-8)
        self.assertAlmostEqual(result['barrel_peak_c'],barrel,places=8)

    def test_zero_loss_uniform_equilibrium(self):
        base = copy.deepcopy(self.base)
        base['pet_zone_c']=[245]*3; base['pet_die_c']=245
        result=model.required_power(base,self.stations,self.zones,air=0,support=0,
                                     overrides={'emissivity':0})
        np.testing.assert_allclose(result['required_watts'],0,atol=1e-7)
        self.assertAlmostEqual(result['barrel_peak_c'],245,places=7)

    def test_non_linear_balance(self):
        result=model.required_power(self.base,self.stations,self.zones)
        for field in ('local_residual_w','sensor_residual_c','global_residual_w'):
            self.assertLess(abs(result[field]),1e-7)
        self.assertFalse(result['energization_authorized'])

    def test_insufficient_power_is_not_control_failure(self):
        result=model.required_power(self.base,self.stations,self.zones,
                                     contact=200,air=15,support=.2)
        self.assertFalse(result['heating_only_feasible'])
        self.assertGreater(result['required_watts'][0],100)
        self.assertGreater(result['required_watts'][3],60)

    def test_valid_condition_has_headroom(self):
        result=model.required_power(self.base,self.stations,self.zones,contact=1000)
        self.assertTrue(result['heating_only_feasible'])

    def test_invalid_target_rejected(self):
        for value in (float('nan'),float('inf'),-274.):
            base=copy.deepcopy(self.base);base['pet_zone_c'][0]=value
            with self.assertRaises(ValueError):
                model.required_power(base,self.stations,self.zones)

    def test_mesh_refinement(self):
        coarse=model.required_power(self.base,self.stations,self.zones,dx=.0025)
        fine=model.required_power(self.base,self.stations,self.zones,dx=.00125)
        self.assertLess(max(abs(a-b) for a,b in zip(coarse['required_watts'],
                                                   fine['required_watts'])),1)


if __name__=='__main__':
    unittest.main()
