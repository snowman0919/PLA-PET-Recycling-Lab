"""The legacy mount screen must use live CAD stations, not barrel endpoints."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'analysis/final_validation'))
import run_calculix_v08 as solver


class MountBindingTest(unittest.TestCase):
    def setUp(self):
        self.original = solver.INPUT
        self.geometry = json.loads((self.original/'geometry_manifest.json').read_text())
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'.build')
        solver.INPUT = Path(self.temp.name)
        self.save()

    def tearDown(self):
        solver.INPUT = self.original
        self.temp.cleanup()

    def save(self):
        (solver.INPUT/'geometry_manifest.json').write_text(json.dumps(self.geometry))

    def deck(self):
        return solver.hot_mount_deck('C_RADIAL_CONTROLLED_AXIAL_EXPANSION',270,pressure_mpa=6)

    def test_supports_and_thrust_are_separate_nodes(self):
        lines = self.deck().splitlines()
        nodes = {}; i = lines.index('*NODE')+1
        while not lines[i].startswith('*'):
            row=lines[i].split(','); nodes[int(row[0])]=float(row[1]); i+=1
        stations=self.geometry['hot_zone_stations']; y=stations['barrel_rear_y_mm']
        for name, target in [('REAR',stations['rear_datum_y_mm']),
                             ('FRONT',stations['front_guide_y_mm']),
                             ('TIP',stations['barrel_die_y_mm'])]:
            node=int(lines[lines.index('*NSET,NSET='+name)+1])
            self.assertAlmostEqual(nodes[node],(y-target)/1000,places=10)
        self.assertTrue(all(len(line.split(','))<=16 for line in lines))
        self.assertIn('TIP,1,',self.deck())
        self.assertNotIn('FRONT,1,',self.deck())

    def test_stale_geometry_rejected(self):
        self.geometry['geometry_source_sha256']='0'*64; self.save()
        with self.assertRaises(ValueError): self.deck()

    def test_shifted_guide_rejected(self):
        self.geometry['hot_zone_stations']['front_guide_y_mm']+=4; self.save()
        with self.assertRaises(ValueError): self.deck()

    def test_shifted_rear_rejected(self):
        self.geometry['hot_zone_stations']['rear_datum_y_mm']+=4; self.save()
        with self.assertRaises(ValueError): self.deck()

    def test_invalid_station_rejected(self):
        for value in [float('nan'),float('inf'),0.,500.]:
            self.geometry['hot_zone_stations']['rear_datum_y_mm']=value; self.save()
            with self.assertRaises(ValueError): self.deck()

if __name__=='__main__': unittest.main()
