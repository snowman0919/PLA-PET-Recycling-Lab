"""Reject stale compiled travel and mismatched simulation traces."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation/openmodelica/postprocess'))
from validate_v08_release import hot_travel_current


class TravelBindingTest(unittest.TestCase):
    def test_live_travel(self):
        self.assertTrue(hot_travel_current([{'axialGrowthMm':1.1,'travelMarginMm':.4}],
                        {'axialTravelMm':1.5},{'cold_axial_travel_mm':1.5}))

    def test_stale_and_invalid_inputs(self):
        good=[{'axialGrowthMm':1.1,'travelMarginMm':.4}]
        for value in [1.3,0.,-1.,float('nan'),float('inf')]:
            self.assertFalse(hot_travel_current(good,{'axialTravelMm':value},
                             {'cold_axial_travel_mm':1.5}))
        self.assertFalse(hot_travel_current([],{'axialTravelMm':1.5},{'cold_axial_travel_mm':1.5}))
        self.assertFalse(hot_travel_current(good,{}, {'cold_axial_travel_mm':1.5}))
        self.assertFalse(hot_travel_current(good,{'axialTravelMm':1.5},{}))

    def test_runtime_override_or_nan_trace(self):
        for margin in [.2,float('nan'),float('inf')]:
            self.assertFalse(hot_travel_current([{'axialGrowthMm':1.1,'travelMarginMm':margin}],
                             {'axialTravelMm':1.5},{'cold_axial_travel_mm':1.5}))

if __name__=='__main__': unittest.main()
