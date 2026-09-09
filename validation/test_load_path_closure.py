"""Regression tests for physical signs, resultants and work-conjugate patch coupling."""
import sys,unittest,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis/final_validation'))
from load_path_contract_v08 import station_loads,support_reactions
from distributing_patch_v08 import rigid_fit_coefficients,resultant_loads,cross_matrix

ST={'shaft_y_min_mm':258.,'bearing_y_mm':[321.,461.],'gear_y_mm':480.,'chain_sprocket_y_mm':264.,'cutter_y_mm':[348.5,361.5,374.5,387.5,400.5,413.5]}
class LoadTests(unittest.TestCase):
    def test_balanced_torque_all_shares(self):
        for sid in ['153','105']:
            for share in [0,.25,.5,.75,1]:
                for d in [-1,1]:self.assertAlmostEqual(sum(r['torque_nm'] for r in station_loads(ST,sid,22,share,d,60,0)),0)
    def test_chain_toward_actual_motor(self):
        for d in [-1,1]:self.assertGreater(station_loads(ST,'153',22,1,d,60,0)[0]['fz_n'],0)
    def test_chain_reversal_same_vertical_force(self):
        a,b=[station_loads(ST,'153',22,1,d,60,0)[0] for d in [-1,1]]
        self.assertAlmostEqual(a['fz_n'],b['fz_n']);self.assertAlmostEqual(a['fx_n'],-b['fx_n'])
    def test_gear_action_reaction(self):
        for d in [-1,1]:
            a=station_loads(ST,'153',22,.5,d,60,0)[1];b=station_loads(ST,'105',22,.5,d,60,0)[0]
            self.assertAlmostEqual(a['fx_n']+b['fx_n'],0);self.assertAlmostEqual(a['fz_n']+b['fz_n'],0)
            self.assertGreater(a['fx_n'],0);self.assertLess(b['fx_n'],0)
    def test_gear_lever_moments(self):
        a=station_loads(ST,'153',22,.5,1,60,0)[1];b=station_loads(ST,'105',22,.5,1,60,0)[0]
        self.assertAlmostEqual(a['torque_nm'],.024*a['fz_n']);self.assertAlmostEqual(b['torque_nm'],-.024*b['fz_n'])
    def test_support_force_moment_equilibrium(self):
        r=station_loads(ST,'153',22,.5,-1,60,5);a,b=ST['bearing_y_mm'];q=support_reactions(r,a,b)
        for axis in ['fx','fz']:
            self.assertAlmostEqual(q['front_'+axis+'_n']+q['rear_'+axis+'_n']+sum(v[axis+'_n'] for v in r),0)
            self.assertAlmostEqual(q['rear_'+axis+'_n']*(b-a)+sum(v[axis+'_n']*(v['y_mm']-a) for v in r),0)
    def test_invalid_share(self):
        for v in [-.1,1.1,float('nan')]:
            with self.assertRaises(ValueError):station_loads(ST,'153',22,v,1,60,0)
    def test_invalid_force_parameter(self):
        for t,s in [(-1,60),(22,-1),(float('inf'),60)]:
            with self.assertRaises(ValueError):station_loads(ST,'153',t,.5,1,s,0)

class PatchTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(28)
        self.pts={i:tuple(p) for i,p in enumerate(rng.normal(size=(17,3))*.015+[.04,.31,.02])}
        self.w={i:float(v) for i,v in enumerate(rng.uniform(.1,1,17))}
        self.o=np.array([0.,.3,0.])
    def test_rigid_mode_recovery(self):
        c=rigid_fit_coefficients(self.pts,self.w,self.o)
        for j in range(6):
            q=np.eye(6)[j];fit=sum(c[n]@(q[:3]+np.cross(q[3:],np.asarray(p)-self.o)) for n,p in self.pts.items())
            np.testing.assert_allclose(fit,q,atol=1e-11)
    def test_load_force_and_moment(self):
        f=np.array([17.,-3.,85.]);m=np.array([2.,22.,-5.])
        nodes=resultant_loads(self.pts,self.w,f,m,self.o)
        np.testing.assert_allclose(sum(nodes.values()),f,atol=1e-9)
        np.testing.assert_allclose(sum(np.cross(np.asarray(self.pts[n])-self.o,v) for n,v in nodes.items()),m,atol=1e-9)
    def test_no_gauge_translational_force(self):
        c=rigid_fit_coefficients(self.pts,self.w,self.o);f={n:row[4] for n,row in c.items()}
        np.testing.assert_allclose(sum(f.values()),[0,0,0],atol=1e-10)
        np.testing.assert_allclose(sum(np.cross(np.asarray(self.pts[n])-self.o,v) for n,v in f.items()),[0,1,0],atol=1e-10)
    def test_work_conjugacy(self):
        rng=np.random.default_rng(7);u={n:rng.normal(size=3)*.001 for n in self.pts};q=np.arange(1.,7.)
        c=rigid_fit_coefficients(self.pts,self.w,self.o);f=resultant_loads(self.pts,self.w,q[:3],q[3:],self.o)
        self.assertAlmostEqual(float(sum(np.dot(f[n],u[n]) for n in self.pts)),float(np.dot(q,sum(c[n]@u[n] for n in self.pts))),places=10)
    def test_degenerate_patch(self):
        with self.assertRaises(ValueError):rigid_fit_coefficients({i:(0,0,i) for i in range(4)},{i:1 for i in range(4)},[0,0,0])
    def test_nonpositive_weight(self):
        self.w[0]=-1
        with self.assertRaises(ValueError):rigid_fit_coefficients(self.pts,self.w,self.o)
    def test_nan_force(self):
        with self.assertRaises(ValueError):resultant_loads(self.pts,self.w,[1,2,float('nan')],[0,0,0],self.o)
if __name__=='__main__':unittest.main(verbosity=2)
