import json,unittest,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from geometry import chain_center
class DesignContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((ROOT/'design/parameters.json').read_text());cls.m=json.loads((ROOT/'design/assembly.json').read_text());cls.r=json.loads((ROOT/'results/engineering.json').read_text())
 def test_existing_power_source_not_upsized(self):
  self.assertEqual(self.p['psu']['nameplate_W'],800);self.assertEqual(self.p['psu']['current_A'],33);self.assertEqual(self.p['psu']['current_derived_ceiling_W'],792);self.assertEqual(self.p['psu']['power_target_W'],500);self.assertEqual(self.p['psu']['body_mm'],[240,120,65]);self.assertEqual(self.p['psu']['V'],24)
 def test_shared_shredder_motor(self):
  self.assertEqual(sum(i['part']=='DRV-M1' for i in self.m['instances']),1)
  self.assertEqual(self.p['S2']['orbit_ratio'],2)
 def test_chain_center_equal_sprockets(self):self.assertAlmostEqual(chain_center(9.525,24,24,94),333.375)
 def test_nonuniform_branch_speeds(self):
  self.assertAlmostEqual(self.r['speeds_rpm']['S1'],21.75);self.assertAlmostEqual(self.r['speeds_rpm']['S2_orbit'],116)
 def test_cutter_phase_key_is_fixed(self):
  cuts=[x for x in self.m['instances'] if x['part'].startswith('S1-CUT-')]
  self.assertEqual(len(cuts),26);self.assertTrue(all(x['rotation'][3]==0 for x in cuts))
  self.assertTrue(all(self.m['parts'][x['part']]['cuts'][1]['at']==[-4,-1,12.0] for x in cuts))
 def test_axial_cutter_clearance(self):self.assertAlmostEqual(self.r['stage1']['axial_gap_nominal_mm'],.2,places=7)
 def test_cycloid_is_a_real_constraint(self):
  self.assertEqual(self.p['S2']['fixed_pins'],self.p['S2']['guide_lobes']+1)
  self.assertGreater(self.r['stage2']['minimum_pin_profile_clearance_mm'],.1)
 def test_buffer_not_marketed_as_usable_volume(self):
  b=self.r['buffer'];self.assertGreater(b['internal_geometric_mL'],300);self.assertLess(b['usable_at75pct_mL'],b['internal_geometric_mL'])
 def test_no_fake_procurement_or_validation_pass(self):
  self.assertEqual(self.p['safety']['procurement'],'HOLD');self.assertEqual(self.p['safety']['DEM'],'NOT_RUN')
 def test_power_allocation_exhaustive_record(self):
  q=self.r['power_allocator_exhaustive'];self.assertEqual(q['cases'],20800);self.assertGreater(q['max_admitted_W'],500);self.assertLessEqual(q['max_admitted_W'],792);self.assertTrue(q['over_target_admitted'])
 def test_nominal_current_capacity(self):self.assertLess(self.r['power']['nominal_all_on_W'],self.r['power']['psu_current_derived_ceiling_W'])
 def test_cooling_convergence(self):
  a,b=self.r['cooling_mesh_check'][-2:];self.assertLess(abs(a['center_cool_time_s']/b['center_cool_time_s']-1),.005)
 def test_source_fields_exist(self):self.assertTrue(all(p.get('source') and p.get('status') for p in self.m['parts'].values()))
 def test_profile_stock_conservation(self):
  import csv
  with (ROOT/'bom/profile_cut_plan.csv').open() as f:
   for row in csv.DictReader(f):self.assertEqual(int(row['stock_mm']),sum(int(row[k]) for k in ['cut_mm','kerf_mm','remaining_mm']))
if __name__=='__main__':unittest.main()
