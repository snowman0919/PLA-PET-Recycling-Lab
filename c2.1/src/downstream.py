"""VP1 Stage 6: downstream filament-quality modules on the existing
die->cooling->puller->winder line.

Frozen datums (unchanged): the extrudate line runs +X at y=275, z=125 from
the EX-DIE exit face (x=540) through the 275 mm COOL-TRAY (x545..820) to the
spring-nip puller at x~829.  The winder stays at x=700, z=220.


This module adds, as REAL geometry integrated into PPR_VP1.step:

1. GAUGE — an inline two-axis filament diameter measurement station
   INSIDE the COOL-TRAY exit section (x 801..811, tray interior
   y 237..313, z 105..133) at the station plane x=809, z=125.  The 4 mm
   gap between the tray exit (x820) and the puller frame (x822..824) is
   real metal (bearing seats/rollers reach x812.9..x822), so an external
   station there was geometry fraud; the tray interior is free air:
   - GAUGE_FRAME: two 3 mm cross straps + wall spacers bolted to the tray
     side walls (above the strand, below the wall top z133).
   - GAUGE_GUIDES: pair of V-guide rollers keeping the strand centered
     under both sensing axes.
   - GAUGE_CONTACT_A: low-contact-force horizontal spring lever + pivot
     carrying ONE Hall probe head (lever-contact candidate, S1/S2
     reference class; contact compliance and TPU deformation are
     explicitly NOT rated here).
   - GAUGE_OPTICAL_B: LED emitter + line sensor on the same plane at
     90 deg to axis A (open-optics candidate, S4 reference class; optical
     axis accuracy on transparent/TPU stock is a separate question).
   Both axes coexist in the CAD because the sensor decision requires the
   comparison harness (docs/decisions/filament-quality-route.md), not
   because both would be purchased.
   - GAUGE_REF_STANDARD: removable pin-gauge holder parked on the tray
     north wall outside face, with three precision pins (1.50 / 1.75 /
     2.00 mm) for on-machine calibration checks.

2. SERVICE-HOPPER — a SWAP part (NOT in the production assembly): remove
   only FEED-BUF while retaining its barrel saddle/clamp. A hollow side-inlet
   chute reaches the common Ø13 throat at x299,y275,z145; its fill mouth is
   outboard at y225,z220, below and clear of S2 metal. The upstream M1/S2
   remains disabled during reference-feed operation. Exported separately.
   Joint sealing, fasteners, service guard and gravity delivery remain HOLD.

3. COOL-DUCT — rails on the tray wall tops and a 100 mm sliding hood with a
   third 80 mm fan envelope and a real through-opening to the strand. The
   two retained side fans also need ports through the tray wall; the VP1
   assembly cuts these into the retained COOL-TRAY. No duct convection
   coefficient or effective cooling length is established by the geometry.

None of these parts is rated: sensor accuracy, nip force, spring loads,
fan airflow and all structural/thermal capacity remain HOLD. The third fan
is an UNRATED 8 W estimate in the modeled 500 W allocator.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq

V = cq.Vector
HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[2]
# Filament line: +X at y=275, z=125 (winder.py frozen datum).
# VP1 Stage 6: the gauge station lives inside the COOL-TRAY exit
# (x806..820, tray interior y237..313, z105..133). The free external gap
# after x820 is too short for a separate station: the driven roller already
# reaches x819 and the idler carrier reaches x823. The 250 mm nominal
# *modeled* forced-cooling run ends at x795, 14 mm upstream of the gauge.
# Tray location and assumed cooling must not be confused with measured
# strand temperature, airflow or dimensional stability.
LINE_Y = 275.0
LINE_Z = 125.0
GAUGE_X = 809.0          # station plane; x>811 above z126 is puller metal
PULLER_NIP_X = 829.0
SENSOR_TO_PULLER_MM = PULLER_NIP_X - GAUGE_X   # 20.0 mm REAL transport delay
GAUGE_INNER_X0 = 805.0
GAUGE_INNER_X1 = 809.0
NOMINAL_FILAMENT_MM = 1.75
REF_PINS_MM = (1.50, 1.75, 2.00)


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _cyl(r, h, x, y, z, axis=(0, 1, 0)):
    return cq.Solid.makeCylinder(r, h, V(x, y, z), V(*axis))





# ---------------------------------------------------------------- gauge ----
# The station is a bracket set bolted INSIDE the COOL-TRAY exit section:
# tray interior is y 237..313, z 105..133 (base z103..105, walls to z133).
# The strand runs at z125; all gauge metal stays inside the free air space
# and clear of the strand envelope (no metal touches z 124..126 except the
# contact anvil, by design).
def gauge_frame():
    """Mounting brackets: two cross straps bolted to the tray side walls
    at x801..803 and x805..807 (strap y 237..313, z 129..131.7 — above the
    strand, below the puller carriage/posts which start at z 131.75, and
    WEST of the adj-roller spring helix whose metal starts at x807), plus
    wall spacer blocks.  No metal below z118 except the guide-roller
    axles."""
    strap_a = _box(801.0, 803.0, 237.0, 313.0, 129.0, 131.7)
    strap_b = _box(805.0, 807.0, 237.0, 313.0, 129.0, 131.7)
    spacer_a = _box(801.0, 803.0, 237.0, 240.0, 118.0, 129.0)
    spacer_b = _box(805.0, 806.5, 310.0, 313.0, 118.0, 129.0)
    return strap_a.fuse(strap_b).fuse(spacer_a).fuse(spacer_b).clean()


def gauge_guides():
    """Two V-guide rollers (dia 8 core, 11 rim, 6 mm wide) on the line at
    the station entry and exit (x = GAUGE_X +/- 1.2), keeping the strand
    centered under both sensing axes.  The rim flanges ride the strand
    below center (contact force unmeasured — HOLD).  Axles span the tray
    interior only (y 237..313)."""
    def v_roller(x):
        core = _cyl(4.0, 6.0, x, LINE_Y - 3.0, LINE_Z - 5.25)
        rim_a = _cyl(5.5, 1.2, x, LINE_Y - 3.0, LINE_Z - 5.25)
        rim_b = _cyl(5.5, 1.2, x, LINE_Y + 1.8, LINE_Z - 5.25)
        return core.fuse(rim_a).fuse(rim_b).clean()
    # axle top (119.75+1.2=120.95) stays clear of the optical heads (z>=121)
    axle_a = _cyl(1.2, 76.0, GAUGE_X - 1.2, 237.0, LINE_Z - 5.25)
    axle_b = _cyl(1.2, 76.0, GAUGE_X + 1.2, 237.0, LINE_Z - 5.25)
    return (v_roller(GAUGE_X - 1.2).fuse(v_roller(GAUGE_X + 1.2))
            .fuse(axle_a).fuse(axle_b).clean())


def gauge_contact_a():
    """Lever-contact axis: a 3 mm horizontal lever pivoting on the strap at
    z 129 (above the strand), with a 1 mm contact anvil reaching DOWN to
    the filament crown at z125.5 and a Hall probe head + magnet target on
    the far lever arm.  Lever ratio 10:1 reduces contact travel 0.25 mm
    per 0.025 mm diameter change; spring rate and contact compliance are
    NOT rated (calibration against the reference pins is the path, not a
    model claim)."""
    pivot = _cyl(2.0, 20.0, GAUGE_X, LINE_Y - 10.0, 129.0)
    lever = _box(GAUGE_INNER_X0, GAUGE_INNER_X1, LINE_Y - 1.5,
                 LINE_Y + 1.5, 127.0, 129.0)
    anvil = _cyl(0.5, 2.0, GAUGE_X, LINE_Y, 125.5, axis=(0, 0, 1))
    probe = _box(GAUGE_INNER_X0, GAUGE_INNER_X1, LINE_Y - 6.0, LINE_Y - 2.0,
                 127.0, 128.9)
    # return spring east of the lever (x>=808.5), clear of strap_b (x<=807)
    spring = _cyl(1.5, 4.0, GAUGE_X - 0.5, LINE_Y, 125.5, axis=(0, 0, 1))
    return pivot.fuse(lever).fuse(anvil).fuse(probe).fuse(spring).clean()


def gauge_optical_b():
    """Open-optics axis at 90 deg to the contact axis: an LED emitter at
    y241 and a line-sensor receiver at y303 on the same z125 plane (both
    6x6x8 heads inside the tray interior; emitter->strand->receiver path
    across the open section).  Transparent/TPU stock accuracy is an open
    question handled by the process-model comparison, not by this CAD."""
    emitter = _box(GAUGE_INNER_X0, GAUGE_INNER_X1, 241.0, 247.0, 121.0, 129.0)
    receiver = _box(GAUGE_INNER_X0, GAUGE_INNER_X1, 297.0, 303.0, 121.0, 129.0)
    aperture_a = _box(GAUGE_X - 0.5, GAUGE_X + 0.5, 247.0, 249.0, 124.0, 126.0)
    aperture_b = _box(GAUGE_X - 0.5, GAUGE_X + 0.5, 295.0, 297.0, 124.0, 126.0)
    return emitter.fuse(receiver).fuse(aperture_a).fuse(aperture_b).clean()


def gauge_ref_standard():
    """Removable pin-gauge holder parked on the tray north wall OUTSIDE
    face (y 315..321): a 6 mm holder bar carrying three precision-ground
    pins (1.50 / 1.75 / 2.00 mm diameter) that thread onto the line
    position for calibration checks.  Pins are the on-machine calibration
    ARTIFACT; micrometer round-trip and U95 <= 0.01 mm verification are
    physical-test work."""
    holder = _box(807.0, 819.0, 315.0, 321.0, 118.0, 124.0)
    pins = None
    for idx, dia in enumerate(REF_PINS_MM):
        pin = _cyl(dia / 2.0, 12.0, 807.0, 316.0 + idx * 1.6, 121.0,
                   axis=(1, 0, 0))
        pins = pin if pins is None else pins.fuse(pin)
    return holder.fuse(pins).clean()
# ------------------------------------------------------- service input ----
# Manual reference-feed inlet must remain OUTBOARD of the S2 screen and
# moving rotor. Only FEED-BUF is removed; its split saddle/clamp on the cold
# barrel remains. This inlet is not a safety guard or a powered conveyor.
def service_hopper():
    """Hollow steel side chute from y225,z220 to Ø13 barrel throat.

    3.5 mm nominal radial neck wall, 3 mm upper walls, 56° nominal
    centerline slope. The Ø20 receiver neck and Ø13 through-hole share
    x299,y275,z145 with FEED-BUF. A bolted/sealed saddle joint needs
    actual fastener detail and physical gravity-flow qualification.
    """
    def ring(radius, y, z):
        return cq.Wire.makePolygon(
            [V(299.0 + radius * math.cos(i * math.pi / 4),
               y + radius * math.sin(i * math.pi / 4), z)
             for i in range(8)], close=True)

    def rectangle(half_x, half_y, y, z):
        points = [(-half_x, -half_y), (0, -half_y),
                  (half_x, -half_y), (half_x, 0),
                  (half_x, half_y), (0, half_y),
                  (-half_x, half_y), (-half_x, 0)]
        return cq.Wire.makePolygon(
            [V(299.0 + x, y + dy, z) for x, dy in points], close=True)

    outer = cq.Solid.makeLoft(
        [ring(10.0, 275.0, 145.0), rectangle(25.0, 12.0, 225.0, 220.0)], True)
    inner = cq.Solid.makeLoft(
        [ring(6.5, 275.0, 143.0), rectangle(22.0, 9.0, 225.0, 222.0)], True)
    # The flange is part of the existing cold barrel saddle joint, not an
    # unsupported wedge extending below it.
    flange = _cyl(14.0, 3.0, 299.0, 275.0, 145.0, axis=(0, 0, 1))
    return outer.fuse(flange).cut(inner).clean()


# ------------------------------------------------------------ cooling -----
def cool_duct():
    """Sliding hood with a genuine top fan aperture over the filament.

    The depicted x610..710 hood can move +/-50 mm on the tray rails without
    touching the gauge at x801. Air volume/heat transfer require measurement.
    The top fan is separately removable; this function is sheet-metal only.
    """
    rail_a = _box(545.0, 820.0, 235.0, 237.0, 133.0, 136.0)
    rail_b = _box(545.0, 820.0, 313.0, 315.0, 133.0, 136.0)
    aperture = _cyl(35.0, 44.0, 670.0, 275.0, 135.0, axis=(0, 0, 1))
    baffle = _box(610.0, 710.0, 237.0, 313.0, 136.0, 139.0).cut(aperture)
    skirt_a = _box(610.0, 613.0, 237.0, 313.0, 110.0, 136.0)
    skirt_b = _box(707.0, 710.0, 237.0, 313.0, 110.0, 136.0)
    return (rail_a.fuse(rail_b).fuse(baffle).fuse(skirt_a).fuse(skirt_b)
            .clean())


def cool_fan_3_ref():
    """80x80x38 fan envelope with open flow ring and supported hub.

    No blade curve, pressure/flow curve, fastener pattern or rating inferred.
    """
    aperture = _cyl(35.0, 40.0, 670.0, 275.0, 138.0, axis=(0, 0, 1))
    frame = _box(630.0, 710.0, 235.0, 315.0, 139.0, 177.0).cut(aperture)
    spokes = (_box(635.0, 705.0, 274.0, 276.0, 157.0, 159.0)
              .fuse(_box(669.0, 671.0, 240.0, 310.0, 157.0, 159.0)))
    hub = _cyl(10.0, 2.0, 670.0, 275.0, 157.0, axis=(0, 0, 1))
    return frame.fuse(spokes).fuse(hub).clean()


def components():
    """Production-assembly downstream parts: (name, solid, group).  The
    SERVICE-HOPPER is NOT here: it swaps for the FEED-BUF stack during
    reference runs and would collide with the retained buffer metal."""
    return [("GAUGE_FRAME", gauge_frame(), "gauge"),
            ("GAUGE_GUIDES", gauge_guides(), "gauge"),
            ("GAUGE_CONTACT_A", gauge_contact_a(), "gauge"),
            ("GAUGE_OPTICAL_B", gauge_optical_b(), "gauge"),
            ("GAUGE_REF_STANDARD", gauge_ref_standard(), "gauge"),
            ("COOL-DUCT", cool_duct(), "cooling"),
            ("COOL-FAN-3_REF", cool_fan_3_ref(), "cooling")]


def swap_parts():
    """Alternate-configuration parts (reference-run swap)."""
    return [("SERVICE-HOPPER", service_hopper(), "feed")]


def _valid(solid):
    return solid.isValid() and len(solid.Solids()) >= 1


def station_interfaces():
    """Interface facts consumed by the process model and wiring/BOM
    builders.  Distances are measured on the frozen datums, not fitted."""
    return {
        "filament_line": {"axis": "+X", "y_mm": LINE_Y, "z_mm": LINE_Z,
                          "die_exit_x_mm": 540.0, "tray_exit_x_mm": 820.0,
                          "gauge_x_mm": GAUGE_X, "puller_nip_x_mm": 829.0},
        "gauge_to_puller_delay": {
            "distance_mm": SENSOR_TO_PULLER_MM,
            "meaning": ("gauge-to-nip travel of already formed strand: "
                        "20.0 / v_mm_s. Feedback dead distance is die exit "
                        "x540 to gauge x809 = 269 mm, not this distance.")},
        "cooling": {"tray_length_mm": 275.0,
                    "modeled_ducted_length_mm": [50.0, 250.0],
                    "effective_length_status": "ASSUMED_NOT_CALIBRATED_BY_CAD",
                    "hood_travel_mm": 100.0,
                    "ports": "two 78x21 mm windows through south tray wall",
                    "fans": "2 legacy references + 1 separate 80x80x38 reference; all UNRATED"},
        "service_input": {
            "configuration": ("SWAP: remove FEED-BUF only, retain its cold "
                              "barrel saddle and clamp. SERVICE-HOPPER "
                              "mates the x299,y275,z145 Ø13 through-hole "
                              "and opens outboard at y225,z220; M1/S2 off "
                              "during reference operation. Joint sealing, "
                              "lid guard and feed delivery remain HOLD."),
            "reason_not_in_assembly": ("production FEED-BUF occupies the "
                                       "same Ø20/Ø13 barrel throat; the "
                                       "alternate is mutually exclusive"),
            "feedstock": "dried, screened reference material only",
            "interlock": "NONE — the hopper is not a guard"},
        "reference_pins_mm": list(REF_PINS_MM),
        "calibration": ("pins + micrometer round-trip; U95 <= 0.01 mm is the "
                        "design assumption, not a measured claim"),
        "sensor_axes": {
            "A_lever_hall": "vertical diameter (contact compliance UNRATED)",
            "B_optical": "horizontal shadow width (transparent/TPU UNRATED)"},
        "wiring_harness": {
            "J5_diameter_gauge": {"axis_A_raw": "analog/Hall input", "axis_B_raw": "shadow ADC input", "supply": "+5V_CTRL / 0V"},
            "J6_aux_and_service": {"fan3_cmd": "24V fan switching circuit TBD; no PWM pin assumed", "service_hopper_detect": "microswitch dry contact to 0V"},
            "controller_core_interface": "gauge_valid, gauge_major_mm, gauge_minor_mm, nominal_puller_speed_mm_s; operating-only quality gate"},
    }


def build_result():
    """Build all parts, export STEP files, and write the geometry result."""
    recs = []
    fails = []
    out_dir = ROOT / "cad" / "parts_stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for name, solid, group in components() + [
            (n, s, g + " (SWAP)") for n, s, g in swap_parts()]:
        ok = _valid(solid)
        recs.append({"name": name, "group": group,
                     "solids": len(solid.Solids()), "valid": solid.isValid(),
                     "bounds": [round(v, 3) for v in _bounds(solid)]})
        if not ok:
            fails.append(name)
        path = out_dir / (name + ".step")
        cq.exporters.export(cq.Compound.makeCompound([solid]), str(path))
        exported.append(str(path.relative_to(REPO)))
    result = {
        "revision": "VP1-STAGE6",
        "status": "DIGITAL_GEOMETRY_PASS_INTERFACE_HOLD" if not fails else
                  "DIGITAL_GEOMETRY_HOLD",
        "parts": recs,
        "exported_step": exported,
        "interfaces": station_interfaces(),
        "holds": [
            "sensor accuracy U95 <= 0.01 mm is a design assumption; pin + "
            "micrometer round-trip is physical-test work",
            "lever contact force / TPU deformation and optical-axis "
            "transparent-stock accuracy are UNRATED",
            "third fan is an UNRATED 8 W power estimate; allocator admission "
            "is not a supply qualification",
            "SERVICE-HOPPER is a manual swap part with NO interlock credit; "
            "it is not a guard and not in the production assembly",
        ],
        "passed": not fails,
    }
    (ROOT / "results" / "downstream_geometry.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if fails:
        raise SystemExit(1)
    return result


def _bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax]


if __name__ == "__main__":
    build_result()
