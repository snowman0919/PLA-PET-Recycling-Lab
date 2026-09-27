"""Behavioral regressions for reference-feed extrusion and gauge geometry."""
import json
import math
import sys
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "src"))
try:
    import cadquery  # noqa: F401
    HAVE_CQ = True
except ImportError:
    HAVE_CQ = False
if HAVE_CQ:
    import downstream as dd
    import winder as w
import process_model as pm
import route_comparison as rc
import power_sim as ps


class PowerGateTests(unittest.TestCase):
    def test_unknown_or_unaffordable_puller_winder_stops_line(self):
        loads = {"fans": 24, "h60": 60, "m1": 196.8, "m2": 43.2, "h100": 100}
        demanded = dict.fromkeys(("fans", "h60", "m1", "m2"), True)
        for aux in (None, 500):
            watts, outcome = ps.admitted_load(600, loads, demanded, aux)
            self.assertEqual(watts, 0)
            self.assertEqual(outcome["state"], "qualification_hold")
        watts, outcome = ps.admitted_load(600, loads, demanded, 76)
        self.assertAlmostEqual(watts, 500)
        self.assertIn("h100_band", outcome)
        watts, outcome = ps.admitted_load(600, loads, demanded, 150)
        self.assertAlmostEqual(watts, 474)
        self.assertNotIn("h100_band", outcome)


class DownstreamGeometryTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_gauge_does_not_intersect_neighboring_metal(self):
        parts = [dd.gauge_frame(), dd.gauge_guides(),
                 dd.gauge_contact_a(), dd.gauge_optical_b(),
                 dd.gauge_ref_standard()]
        for i, left in enumerate(parts):
            for right in parts[i + 1:]:
                self.assertLess(left.intersect(right).Volume(), 0.001)
        for neighbor in (w.pull_roller_adj(), w.pull_roller_fixed(),
                         w.pull_frame()):
            self.assertLess(parts[0].intersect(neighbor).Volume(), 0.001)
    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_cooling_fans_have_open_air_paths_through_baffle_and_tray(self):
        import build_machine_integration as machine
        cfg = json.loads((R / "design/machine_integration.json").read_text())
        master = json.loads((R.parent / "design/assembly.json").read_text())
        tray = next(p["shape"] for p in machine.legacy_parts(master, cfg)
                    if p["name"] == "COOL-TRAY_001")
        for x in (610, 750):
            air = cadquery.Solid.makeCylinder(
                1.5, 14, cadquery.Vector(x, 227, 120),
                cadquery.Vector(0, 1, 0))
            self.assertLess(air.intersect(tray).Volume(), 0.001)
        duct, fan = dd.cool_duct(), dd.cool_fan_3_ref()
        self.assertEqual(fan.BoundingBox().xlen, 80)
        self.assertEqual(fan.BoundingBox().ylen, 80)
        self.assertEqual(fan.BoundingBox().zlen, 38)
        self.assertLess(duct.intersect(fan).Volume(), 0.001)
        air = cadquery.Solid.makeCylinder(
            1.5, 47, cadquery.Vector(655, 270, 131),
            cadquery.Vector(0, 0, 1))
        self.assertLess(air.intersect(duct).Volume(), 0.001)
        self.assertLess(air.intersect(fan).Volume(), 0.001)
        # A third air passage does not prove convection or cooling capacity.
    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_nominal_filament_contacts_both_nip_rollers_not_their_frame(self):
        strand = cadquery.Solid.makeCylinder(
            0.875, 10, cadquery.Vector(824, 275, 125),
            cadquery.Vector(1, 0, 0))
        for roller in (w.pull_roller_fixed(), w.pull_roller_adj()):
            self.assertGreater(roller.intersect(strand).Volume(), 0.1)
            self.assertLess(roller.intersect(w.pull_frame()).Volume(), 0.001)
        self.assertLess(w.pull_frame().intersect(strand).Volume(), 0.001)
        stop = w.pull_nip_stop()
        self.assertLess(stop.intersect(w.pull_roller_adj()).Volume(), 0.001)
        self.assertLess(stop.intersect(w.pull_frame()).Volume(), 0.001)

    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_winder_loose_bore_and_friction_faces_do_not_interfere(self):
        shaft, spool, clutch = (w.spool_shaft(), w.spool_drum(),
                                w.spool_clutch_ref())
        self.assertTrue(shaft.isValid() and spool.isValid() and clutch.isValid())
        self.assertLess(shaft.intersect(spool).Volume(), 0.001)
        self.assertLess(shaft.intersect(clutch).Volume(), 0.001)
        self.assertLess(clutch.intersect(w.spool_flange_l()).Volume(), 0.001)
        self.assertAlmostEqual(clutch.BoundingBox().ymax,
                               w.spool_flange_l().BoundingBox().ymin)

    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_spool_axial_stops_react_clutch_and_capture_loose_flange(self):
        shaft = w.spool_shaft()
        left, right, washer = w.spool_retention()
        collar, flange = w.spool_clutch_ref(), w.spool_flange_r()
        # External rings sit in shaft grooves, not a full-diameter journal.
        for ring in (left, right):
            self.assertTrue(ring.isValid())
            self.assertLess(shaft.intersect(ring).Volume(), 0.001)
            self.assertLess(w.spool_bearing_blocks().intersect(ring).Volume(), 0.001)
        self.assertLess(shaft.intersect(washer).Volume(), 0.001)
        self.assertLess(right.intersect(washer).Volume(), 0.001)
        self.assertLess(washer.intersect(flange).Volume(), 0.001)
        self.assertAlmostEqual(left.BoundingBox().ymax, collar.BoundingBox().ymin)
        self.assertAlmostEqual(flange.BoundingBox().ymax, washer.BoundingBox().ymin)
        self.assertAlmostEqual(washer.BoundingBox().ymax, right.BoundingBox().ymin)
        # A 0.5 mm rightward escape must meet a positive stop; the original
        # flange could move 3 mm without contacting stationary metal.
        self.assertGreater(
            flange.translate((0, 0.5, 0)).intersect(washer).Volume(), 0.1)
        # Both split rings occupy their grooves rather than floating outside
        # the journal; a local probe at radius 7.5 intersects ring, not shaft.
        for y, ring in ((96.5, left), (168.5, right)):
            probe = cadquery.Solid.makeCylinder(
                0.1, 0.2, cadquery.Vector(706, y - 0.1, 224.5),
                cadquery.Vector(0, 1, 0))
            self.assertLess(shaft.intersect(probe).Volume(), 0.001)
            self.assertGreater(ring.intersect(probe).Volume(), 0.001)

    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_pull_and_cooling_tray_share_rear_metal_frame_path(self):
        import build_machine_integration as machine
        cfg = json.loads((R / "design/machine_integration.json").read_text())
        master = json.loads((R.parent / "design/assembly.json").read_text())
        placed = {p["name"]: p["shape"]
                  for p in machine.legacy_parts(master, cfg)}
        rack, pull = w.pull_cool_mount(), w.pull_frame()
        self.assertTrue(rack.isValid())
        self.assertEqual(len(rack.Solids()), 1)
        for target, point, span in (
                (placed["FR-2040-400_002"], (630, 380, 110), (0.02, 2, 2)),
                (placed["COOL-TRAY_001"], (700, 307, 103), (2, 2, 0.02)),
                (pull, (832, 275, 100), (2, 2, 0.02))):
            probe = cadquery.Solid.makeBox(
                *span, cadquery.Vector(*(v - s / 2 for v, s in zip(point, span))))
            self.assertGreater(rack.intersect(probe).Volume(), 0.001)
            self.assertGreater(target.intersect(probe).Volume(), 0.001)
            self.assertLess(rack.intersect(target).Volume(), 0.001)
        for y in (268, 282):
            recessed_bolt = cadquery.Solid.makeCylinder(
                2.25, 7, cadquery.Vector(833, y, 97),
                cadquery.Vector(0, 0, 1))
            self.assertLess(recessed_bolt.intersect(rack).Volume(), 0.001)
            self.assertLess(recessed_bolt.intersect(pull).Volume(), 0.001)
            self.assertLess(recessed_bolt.intersect(
                w.pull_roller_fixed()).Volume(), 0.001)
        air = cadquery.Solid.makeBox(
            10, 8, 8, cadquery.Vector(700, 371, 86))
        self.assertLess(rack.intersect(air).Volume(), 0.001)
        self.assertLess(rack.intersect(w.pull_roller_fixed()).Volume(), 0.001)

    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_winder_load_path_and_hollow_spool_clear_rotating_faces(self):
        import build_machine_integration as machine
        cfg = json.loads((R / "design/machine_integration.json").read_text())
        master = json.loads((R.parent / "design/assembly.json").read_text())
        front = next(p["shape"] for p in machine.legacy_parts(master, cfg)
                     if p["name"] == "FR-2020-400_001")
        mount, bearings, motor = (w.winder_mount(), w.spool_bearing_blocks(),
                                  w.winder_motor_ref())
        self.assertTrue(mount.isValid())
        self.assertEqual(len(mount.Solids()), 1)
        # Each probe crosses the actual face; a floating reference loses it.
        for target, point, span in (
                (front, (620, 60, 190), (2, 0.02, 2)),
                (bearings, (700, 92, 208), (2, 2, 0.02)),
                (bearings, (700, 174, 208), (2, 2, 0.02)),
                (motor, (700, 200, 200), (2, 2, 0.02))):
            probe = cadquery.Solid.makeBox(
                *span, cadquery.Vector(*(v - s / 2 for v, s in zip(point, span))))
            self.assertGreater(mount.intersect(probe).Volume(), 0.001)
            self.assertGreater(target.intersect(probe).Volume(), 0.001)
            self.assertLess(mount.intersect(target).Volume(), 0.001)
        for z in (185, 200):
            clearance = cadquery.Solid.makeCylinder(
                2.75, 4, cadquery.Vector(620, 60, z),
                cadquery.Vector(0, 1, 0))
            self.assertLess(mount.intersect(clearance).Volume(), 0.001)
        for moving in (w.spool_drum(), w.spool_flange_l(),
                       w.spool_flange_r(), w.spool_shaft()):
            self.assertLess(mount.intersect(moving).Volume(), 0.001)
        drum = w.spool_drum()
        self.assertEqual(len(drum.Solids()), 1)
        self.assertLess(drum.Volume() * 0.00785, 500)  # g at steel proxy rho
        middle = cadquery.Solid.makeCylinder(
            5, 2, cadquery.Vector(720, 134, 220), cadquery.Vector(0, 1, 0))
        self.assertLess(drum.intersect(middle).Volume(), 0.001)
        web = cadquery.Solid.makeCylinder(
            2, 2, cadquery.Vector(720, 109, 220), cadquery.Vector(0, 1, 0))
        self.assertGreater(drum.intersect(web).Volume(), 1)

    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_reference_hopper_has_open_throat_and_clears_retained_machine(self):
        import build_machine_integration as machine
        hopper = dd.service_hopper()
        cfg = json.loads((R / "design/machine_integration.json").read_text())
        master = json.loads((R.parent / "design/assembly.json").read_text())
        # A Ø4 reference pellet must see a real channel, not a solid loft.
        for z in range(146, 220, 5):
            y = 275 - 50 * (z - 145) / 75
            pellet = cadquery.Solid.makeSphere(2, cadquery.Vector(299, y, z))
            self.assertLess(pellet.intersect(hopper).Volume(), 0.01, z)
        # Remove only the buffer shell. The saddle and S2 supports remain.
        adjacent = machine.c21_parts(cfg) + machine.legacy_parts(master, cfg)
        for item in adjacent:
            if item["name"] == "FEED-BUF_001":
                continue
            if machine.bbox_overlap(hopper, item["shape"]):
                overlap = hopper.intersect(item["shape"]).Volume()
                self.assertLess(overlap, 0.05, item["name"])


class ProcessModelPhysicsTests(unittest.TestCase):
    def test_mass_balance_for_planned_rate_and_other_materials(self):
        for material, props in pm.MATERIALS.items():
            v = pm.nominal_speed_mm_s(material)
            d = pm.steady_diameter_mm(pm.NOMINAL_MDOT_G_S, props["rho_s"], v)
            self.assertAlmostEqual(d, 1.75, places=8)
        self.assertAlmostEqual(pm.nominal_speed_mm_s("PLA"), 9.31, delta=0.02)
        d1 = pm.steady_diameter_mm(pm.NOMINAL_MDOT_G_S, 1240, 10)
        d2 = pm.steady_diameter_mm(pm.NOMINAL_MDOT_G_S, 1240, 20)
        self.assertAlmostEqual(d1 / d2, math.sqrt(2), places=7)

    def test_step_flow_cannot_be_measured_before_die_to_gauge_transit(self):
        p = pm.LineParams(fans_on=3)
        def step(e):
            return {**e, "mdot_factor": 1.2 if e["t_s"] >= 10 else 1.0}
        samples = pm.simulate(p, t_total_s=70, disturbance=step)
        before = [s for s in samples if s["t_created_s"] < 10]
        after = [s for s in samples if s["t_created_s"] >= 10]
        self.assertTrue(before and after)
        self.assertLess(before[-1]["d_true_mm"], 1.78)
        self.assertGreater(after[0]["d_true_mm"], 1.90)
        self.assertGreater(after[0]["t_gauge_s"], 10 + 25)
        self.assertLess(after[0]["t_gauge_s"], 10 + 33)
        self.assertGreater(after[0]["t_s"] - after[0]["t_gauge_s"], 1.5)
        self.assertLess(after[0]["t_s"] - after[0]["t_gauge_s"], 3.0)

    def test_duct_length_and_fans_change_actual_gauge_readiness(self):
        long_duct = pm.simulate(pm.LineParams(ducted_mm=250, fans_on=3), 70)
        short_duct = pm.simulate(pm.LineParams(ducted_mm=50, fans_on=3), 70)
        passive = pm.simulate(pm.LineParams(ducted_mm=250, fans_on=0), 70)
        self.assertLess(long_duct[0]["core_C"], short_duct[0]["core_C"])
        self.assertLess(short_duct[0]["core_C"], passive[0]["core_C"])
        self.assertTrue(long_duct[0]["thermal_ready"])
        self.assertFalse(short_duct[0]["thermal_ready"])
        self.assertEqual(pm.quality_summary(short_duct)["in_spec_length_mm"], 0)

    def test_unmeasured_and_unready_lengths_never_receive_credit(self):
        p = pm.LineParams()
        def dropout(e):
            return {**e, "sensor_dropout": 40 <= e["t_s"] < 45}
        samples = pm.simulate(p, 75, disturbance=dropout)
        quality = pm.quality_summary(samples)
        self.assertGreater(quality["unmeasured_length_mm"], 40)
        self.assertLess(quality["in_spec_length_mm"], quality["total_length_mm"])
        poor_cooling = pm.quality_summary(pm.simulate(
            pm.LineParams(ducted_mm=50), 75))
        self.assertGreater(poor_cooling["thermally_unready_length_mm"], 0)
        self.assertEqual(poor_cooling["in_spec_length_mm"], 0)

    def test_barrel_loss_changes_heat_and_mass_flow_under_staging(self):
        p = pm.LineParams()
        def heat_loss(e):
            return {**e, "barrel_loss_extra_W": 150 if e["t_s"] >= 10 else 0}
        base = pm.simulate(p, 110)
        disturbed = pm.simulate(p, 110, disturbance=heat_loss)
        at_60 = lambda xs: min(xs, key=lambda s: abs(s["t_created_s"] - 60))
        self.assertLess(at_60(disturbed)["barrel_birth_C"],
                        at_60(base)["barrel_birth_C"])
        self.assertLess(at_60(disturbed)["mdot_g_s"], at_60(base)["mdot_g_s"])
        self.assertLessEqual(max(s["heater_W"] for s in disturbed), 160)

    def test_clutch_limits_tension_as_spool_grows_and_fault_slips(self):
        p = pm.LineParams()
        def commanded_overrun(e):
            return {**e, "tension_N": 10.0}
        safe = pm.simulate(p, 80, disturbance=commanded_overrun)
        self.assertGreater(safe[-1]["spool_radius_mm"], safe[0]["spool_radius_mm"])
        self.assertLess(safe[-1]["tension_N"], safe[0]["tension_N"])
        self.assertTrue(all(s["slip"] == 0 for s in safe))
        def failed_clutch(e):
            return {**e, "clutch_failed": True, "tension_N": 10.0}
        failed = pm.simulate(p, 80, disturbance=failed_clutch)
        self.assertGreater(failed[-1]["slip"], 0)
        self.assertGreater(failed[-1]["d_true_mm"], safe[-1]["d_true_mm"])


class FeedbackTests(unittest.TestCase):
    def test_missing_gauge_holds_last_command(self):
        ctrl = rc.PIController(v_nominal=9.3)
        updated = ctrl(1.90, 10.0)
        self.assertGreater(updated, 9.3)
        self.assertEqual(ctrl(None, 10.1), updated)
        self.assertEqual(ctrl(None, 11.0), updated)

    def test_sensor_dropout_latches_feedback_and_cuts_product_length(self):
        fixed, _ = rc.run_route("fixed", rc.fixed_speed_controller, "transient")
        feedback, samples = rc.run_route(
            "feedback", lambda p: rc.PIController(p.v_line_mm_s), "transient")
        self.assertGreaterEqual(feedback["controller_halted_at_s"], 145.9)
        self.assertLessEqual(feedback["controller_halted_at_s"], 146.1)
        self.assertLess(feedback["in_spec_length_mm"], fixed["in_spec_length_mm"])
        self.assertGreater(feedback["pending_unqualified_length_mm"], 269)
        self.assertTrue(all(s["t_s"] < 146 for s in samples))
        ctrl = rc.PIController(9.3)
        ctrl(1.9, 10)
        self.assertEqual(ctrl(None, 11.1), 0.0)
        self.assertEqual(ctrl(1.75, 11.2), 0.0)

    def test_sustained_flow_offset_improves_qualified_length(self):
        fixed, _ = rc.run_route("C", rc.fixed_speed_controller,
                                "sustained_offset")
        feedback, samples = rc.run_route(
            "A", lambda p: rc.PIController(p.v_line_mm_s),
            "sustained_offset")
        self.assertEqual(fixed["in_spec_length_mm"], 0)
        self.assertGreater(feedback["in_spec_fraction"], 0.5)
        self.assertLess(abs(samples[-1]["d_true_mm"] - 1.75), 0.02)


if __name__ == "__main__":
    unittest.main()
