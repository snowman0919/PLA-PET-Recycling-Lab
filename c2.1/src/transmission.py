"""C2.1 S2 one-DOF fixed-ring cycloid transmission checks.

Angles are absolute in frame F0. Positive XZ angle maps +X toward +Z and is
a right-hand rotation about -Y; CadQuery +Y therefore uses the negative angle.
Geometry is millimetres, speed radians/second, torque N*m. Results are kinematic
evidence, never shredding-performance or hardware-rating evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Transmission:
    q: int = 8
    eccentric_mm: float = 7.0
    input_rpm: float = 120.0
    rotor_tip_diameter_mm: float = 110.0
    chamber_diameter_mm: float = 125.6
    output_pin_pitch_radius_mm: float = 38.0
    output_pin_count: int = 6
    output_roller_radius_mm: float = 5.0
    coupling_radial_clearance_mm: float = 0.20

    def __post_init__(self):
        if self.q < 2 or self.output_pin_count < 3:
            raise ValueError("q>=2 and at least three output pins are required")
        if min(self.eccentric_mm, self.input_rpm, self.rotor_tip_diameter_mm,
               self.chamber_diameter_mm, self.output_pin_pitch_radius_mm,
               self.output_roller_radius_mm, self.coupling_radial_clearance_mm) <= 0:
            raise ValueError("positive dimensions and speed required")
        if self.chamber_diameter_mm/2 <= self.rotor_tip_diameter_mm/2 + self.eccentric_mm:
            raise ValueError("rotor orbital envelope must fit inside chamber")

    @property
    def omega_in(self):
        return self.input_rpm * 2*math.pi/60

    @property
    def output_window_radius_mm(self):
        return self.output_roller_radius_mm + self.eccentric_mm + self.coupling_radial_clearance_mm


def rotation(angle: float) -> np.ndarray:
    return np.array([[math.cos(angle), -math.sin(angle)],
                     [math.sin(angle), math.cos(angle)]])


def cad_y_degrees_for_xz(angle: float) -> float:
    """CadQuery +Y right-hand angle that realizes numerical R(angle) in XZ."""
    return -math.degrees(angle)


def cad_positive_y_rotation_xz(point_xz, angle_deg: float) -> np.ndarray:
    """Independent right-hand +Y transform used by frame regression tests."""
    x, z = np.asarray(point_xz, dtype=float)
    a = math.radians(angle_deg)
    return np.array([math.cos(a)*x+math.sin(a)*z,
                     -math.sin(a)*x+math.cos(a)*z])


def pose(theta: float, c: Transmission) -> dict:
    """Input θ, disc/rotor/output φ=-θ/q, fixed ring=0."""
    phi = -theta/c.q
    return {
        "input_angle_rad": theta,
        "orbit_center_mm": [c.eccentric_mm*math.cos(theta), c.eccentric_mm*math.sin(theta)],
        "rotor_angle_rad": phi,
        "output_carrier_angle_rad": phi,
        "fixed_ring_angle_rad": 0.0,
    }


def rotor_point(point_local_mm, theta: float, c: Transmission) -> np.ndarray:
    p = np.asarray(point_local_mm, dtype=float)
    center = c.eccentric_mm*np.array([math.cos(theta), math.sin(theta)])
    return center + rotation(-theta/c.q) @ p


def rotor_point_velocity(point_local_mm, theta: float, c: Transmission) -> np.ndarray:
    p = rotation(-theta/c.q) @ np.asarray(point_local_mm, dtype=float)
    orbit = c.eccentric_mm*c.omega_in*np.array([-math.sin(theta), math.cos(theta)])
    spin = (-c.omega_in/c.q)*np.array([-p[1], p[0]])
    return orbit + spin


def external_mesh_sign(meshes: int, input_sign: int = 1) -> int:
    if meshes < 0 or input_sign not in (-1, 1):
        raise ValueError("nonnegative mesh count and signed input required")
    return input_sign * (-1 if meshes % 2 else 1)


def coupling(theta: float, c: Transmission) -> dict:
    """Pin centre relative to the window in their common rotating frame.

    Rotor and carrier share phi=-theta/q, so the relative vector turns at
    omega*(1+1/q), not omega. Positive clearance proves non-interference only;
    Rigid first-contact take-up is calculated separately; elastic sharing,
    contact stress, wear and component rating remain HOLD.
    """
    relative_world = -c.eccentric_mm*np.array([math.cos(theta), math.sin(theta)])
    relative_rotor = rotation(theta/c.q) @ relative_world
    speed = c.eccentric_mm*c.omega_in*(1+1/c.q)
    relative_spin_rpm = -speed/c.output_roller_radius_mm*60/(2*math.pi)
    carrier_rpm = -c.input_rpm/c.q
    return {
        "relative_center_rotor_frame_mm": relative_rotor.tolist(),
        "center_excursion_mm": float(np.linalg.norm(relative_rotor)),
        "diametral_stroke_mm": 2*c.eccentric_mm,
        "window_radius_mm": c.output_window_radius_mm,
        "roller_radius_mm": c.output_roller_radius_mm,
        "nominal_radial_clearance_mm": c.output_window_radius_mm-c.output_roller_radius_mm-float(np.linalg.norm(relative_rotor)),
        "relative_center_speed_mm_s": speed,
        "ideal_roller_spin_relative_carrier_rpm": relative_spin_rpm,
        "ideal_roller_absolute_spin_rpm": carrier_rpm+relative_spin_rpm,
        "ideal_spin_assumption": "NO_SLIP_SINGLE_CONTACT_ONLY_NOT_MEASURED_OR_RATED",
        "loaded_contact_transfer_status": "RIGID_FIRST_CONTACT_EQUILIBRIUM_PASS_ELASTIC_SHARING_RATING_HOLD",
        "rating_status": "HOLD_UNVERIFIED_ROLLER_BEARING_AND_CONTACT_PRESSURE",
    }


def loaded_contact_takeup(theta: float, c: Transmission, direction: int = 1,
                          output_torque_Nm: float = 8.0) -> dict:
    """Rigid-clearance first contact and single-normal output equilibrium.

    The carrier is rotated relative to the rotor until one roller reaches its
    window. This closes the kinematic backlash question, but elastic sharing,
    Hertz stress, friction, wear and rating remain unverified.
    """
    if direction not in (-1,1) or output_torque_Nm <= 0:
        raise ValueError("signed direction and positive torque required")
    pitch=c.output_pin_pitch_radius_mm
    pins=np.array([[pitch*math.cos(2*math.pi*j/c.output_pin_count),
                    pitch*math.sin(2*math.pi*j/c.output_pin_count)]
                   for j in range(c.output_pin_count)])
    phi=-theta/c.q
    eccentric=c.eccentric_mm*np.array([math.cos(theta),math.sin(theta)])
    offset=rotation(-phi)@eccentric
    limit=c.output_window_radius_mm-c.output_roller_radius_mm

    def vectors(delta):
        return pins@rotation(delta).T-pins-offset

    def residual(magnitude):
        return float(np.linalg.norm(vectors(direction*magnitude),axis=1).max()-limit)

    lo,hi=0.0,1e-6
    while residual(hi)<0 and hi<math.pi:
        hi*=2
    if hi>=math.pi:
        raise ValueError("No pin/window contact found within half a turn")
    for _ in range(64):
        mid=(lo+hi)/2
        if residual(mid)<0:lo=mid
        else:hi=mid
    delta=direction*hi
    d=vectors(delta)
    distances=np.linalg.norm(d,axis=1)
    pin_index=int(np.argmax(distances))
    normal=d[pin_index]/distances[pin_index]
    carrier_pin=rotation(delta)@pins[pin_index]
    force_direction=-normal
    signed_lever_mm=float(carrier_pin[0]*force_direction[1]
                          -carrier_pin[1]*force_direction[0])
    force_N=output_torque_Nm/(abs(signed_lever_mm)/1000)
    return {
        "theta_rad":theta,"direction":direction,
        "relative_phase_takeup_rad":delta,
        "relative_phase_takeup_deg":math.degrees(delta),
        "first_contact_pin_index":pin_index,
        "pin_center_distances_mm":distances.tolist(),
        "contact_center_limit_mm":limit,
        "contact_normal_rotor_frame":normal.tolist(),
        "signed_unit_force_lever_mm":signed_lever_mm,
        "output_torque_Nm":output_torque_Nm,
        "single_contact_normal_force_N":force_N,
        "torque_equilibrium_residual_Nm":force_N*abs(signed_lever_mm)/1000-output_torque_Nm,
        "contact_model":"RIGID_FIRST_CONTACT_SINGLE_NORMAL_NO_FRICTION",
        "rating_status":"HOLD_ELASTIC_SHARING_HERTZ_STRESS_FRICTION_WEAR_AND_ROLLER_RATING",
    }


def loaded_contact_sweep(c: Transmission, output_torques_Nm=(1.0,3.0,8.0), positions: int=193) -> dict:
    if positions<3:
        raise ValueError("at least three positions required")
    samples=[loaded_contact_takeup(float(theta),c,direction,1.0)
             for theta in np.linspace(0,2*math.pi*c.q,positions) for direction in (-1,1)]
    force_per_Nm=[r['single_contact_normal_force_N'] for r in samples]
    phase=[abs(r['relative_phase_takeup_deg']) for r in samples]
    return {
        "input_turns":c.q,"positions":positions,"directions_per_position":2,
        "samples":len(samples),"clearance_mm":c.coupling_radial_clearance_mm,
        "phase_takeup_deg":{"min":min(phase),"max":max(phase)},
        "single_contact_force_per_output_Nm_N":{"min":min(force_per_Nm),"max":max(force_per_Nm)},
        "torque_sensitivity":[{"output_torque_Nm":t,
                                "single_contact_force_range_N":[t*min(force_per_Nm),t*max(force_per_Nm)]}
                               for t in output_torques_Nm],
        "maximum_equilibrium_residual_Nm":max(abs(r['torque_equilibrium_residual_Nm']) for r in samples),
        "result":"RIGID_FIRST_CONTACT_EQUILIBRIUM_PASS_RATING_HOLD",
        "not_verified":["elastic_pin_load_sharing","contact_pressure","friction_and_slip",
                        "roller_bearing_rating","window_edge_stress","manufacturing_tolerance_and_wear"],
    }


def ideal_virtual_work(c: Transmission, output_resisting_torque_Nm: float = 8.0) -> dict:
    """Signed power on the mechanism; ideal lossless accounting only."""
    if output_resisting_torque_Nm <= 0:
        raise ValueError("positive resisting torque magnitude required")
    wi = c.omega_in
    wo = -wi/c.q
    ti = output_resisting_torque_Nm/c.q
    to = output_resisting_torque_Nm
    tr = -(ti+to)  # static torque balance; fixed ring carries this reaction.
    powers = {"input_W": ti*wi, "output_load_on_mechanism_W": to*wo,
              "fixed_ring_W": tr*0.0}
    return {
        "omega_rad_s": {"input": wi, "output_carrier": wo, "fixed_ring": 0.0},
        "torque_on_mechanism_Nm": {"input": ti, "output_load": to, "fixed_ring_reaction": tr},
        "power_on_mechanism_W": powers,
        "power_residual_W": sum(powers.values()),
        "torque_balance_residual_Nm": ti+to+tr,
        "evidence": "IDEAL_VIRTUAL_WORK_NO_EFFICIENCY_OR_RATING",
    }


def rotor_force_virtual_work(force_xz_N, point_local_mm, theta: float, c: Transmission,
                              external_moment_Nm: float = 0.0) -> dict:
    """Map a force/moment on the orbiting rotor to the single input DOF."""
    force = np.asarray(force_xz_N, dtype=float)
    point = np.asarray(point_local_mm, dtype=float)
    velocity_m_s = rotor_point_velocity(point, theta, c)/1000
    phi_dot = -c.omega_in/c.q
    load_power = float(force@velocity_m_s + external_moment_Nm*phi_dot)
    generalized_load_torque = load_power/c.omega_in
    # The balancing input torque is the opposite generalized load torque.
    balancing_input_torque = -generalized_load_torque
    input_power = balancing_input_torque*c.omega_in
    return {
        "force_xz_N": force.tolist(), "point_local_mm": point.tolist(),
        "theta_rad": theta, "external_moment_Nm": external_moment_Nm,
        "contact_velocity_xz_mm_s": (velocity_m_s*1000).tolist(),
        "force_power_W": float(force@velocity_m_s),
        "moment_power_W": external_moment_Nm*phi_dot,
        "load_power_W": load_power,
        "generalized_load_torque_at_input_Nm": generalized_load_torque,
        "balancing_input_torque_Nm": balancing_input_torque,
        "input_power_W": input_power,
        "power_residual_W": input_power+load_power,
        "evidence": "POINT_FORCE_JACOBIAN_AND_EXTERNAL_MOMENT_NOT_LOAD_SIZING",
    }


def validate_case(c: Transmission, samples_per_orbit: int = 96) -> dict:
    theta = np.linspace(0, 2*math.pi*c.q, samples_per_orbit*c.q+1)
    p = np.array([c.rotor_tip_diameter_mm/2, 0.0])
    closure = float(np.linalg.norm(rotor_point(p, theta[-1], c)-rotor_point(p, 0, c)))
    one_orbit = float(np.linalg.norm(rotor_point(p, 2*math.pi, c)-rotor_point(p, 0, c)))
    dt = 1e-6
    velocity_errors = []
    margins = []
    for th in theta:
        h = c.omega_in*dt
        fd = (rotor_point(p, th+h, c)-rotor_point(p, th-h, c))/(2*dt)
        velocity_errors.append(float(np.linalg.norm(fd-rotor_point_velocity(p, th, c))))
        margins.append(coupling(float(th), c)["nominal_radial_clearance_mm"])
    wall_gap = c.chamber_diameter_mm/2-(c.rotor_tip_diameter_mm/2+c.eccentric_mm)
    return {
        "parameters": asdict(c),
        "signed_speed_rpm": {"input": c.input_rpm, "orbit": c.input_rpm,
                             "rotor_self": -c.input_rpm/c.q,
                             "output_carrier": -c.input_rpm/c.q, "fixed_ring": 0.0},
        "full_labeled_cycle_input_turns": c.q,
        "sampled_positions": len(theta),
        "full_cycle_closure_error_mm": closure,
        "one_orbit_labeled_point_displacement_mm": one_orbit,
        "minimum_nominal_coupling_clearance_mm": min(margins),
        "loaded_output_contact_status": "HOLD_PHASE_TAKEUP_AND_CONTACT_SHARING_UNVERIFIED",
        "maximum_velocity_fd_error_mm_s": max(velocity_errors),
        "maximum_relative_coupling_center_speed_mm_s": c.eccentric_mm*c.omega_in*(1+1/c.q),
        "rotor_to_chamber_radial_gap_mm": wall_gap,
        "kinematic_clearance_passed": min(margins) >= c.coupling_radial_clearance_mm-1e-9,
        "passed": closure < 1e-9 and one_orbit > 1e-3 and min(margins) >= c.coupling_radial_clearance_mm-1e-9
                  and max(velocity_errors) < 1e-5 and wall_gap > 0,
        "evidence": "DETERMINISTIC_KINEMATICS_NOT_SHREDDING_PERFORMANCE",
    }


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")


def main():
    cases = [validate_case(Transmission(q=q, eccentric_mm=e,
                                        chamber_diameter_mm=110+2*(e+0.8)))
             for e in (7.0, 10.0, 14.0) for q in (6, 8, 16)]
    nominal = Transmission()
    angles = np.linspace(0, 2*math.pi*nominal.q, nominal.q*24+1)
    motion = [{**pose(float(t), nominal), "coupling": coupling(float(t), nominal)} for t in angles]
    summary = {
        "revision": "C2.1",
        "mechanism": "SINGLE_DOF_FIXED_RING_CYCLOID_WITH_OUTPUT_PIN_OFFSET_ACCOMMODATION",
        "independent_drive_dof": 1,
        "roles": {"input": "M1-driven concentric shaft and eccentric journal",
                  "output": "fixed-axis pin carrier witness/load-extraction candidate, signed -1/q; not independently powered",
                  "carrier": "output pin carrier centred on F0 origin",
                  "fixed_reaction": "q+1 stationary ring pins and metal support plates",
                  "rotor_connection": "single fused CAD envelope for cycloid disc, hook rotor and coupling web; physical bolts/retention HOLD"},
        "gear_mesh_parity": {"one_external_mesh": external_mesh_sign(1),
                             "one_idler_two_external_meshes": external_mesh_sign(2)},
        "nominal_coupling": coupling(0.0, nominal),
        "loaded_contact_takeup": loaded_contact_sweep(nominal),
        "ideal_virtual_work": ideal_virtual_work(nominal),
        "rotor_force_virtual_work": rotor_force_virtual_work([-120.0, 35.0], [55.0, 0.0], 0.71, nominal, 2.0),
        "cases": cases,
        "all_cases_passed": all(x["passed"] for x in cases),
        "performance_gate": "BLOCKED_PERFORMANCE_DATA",
        "loaded_output_contact": "RIGID_FIRST_CONTACT_EQUILIBRIUM_PASS_RATING_HOLD",
        "bearing_and_coupling_rating": "HOLD",
        "procurement": "HOLD", "fabrication": "HOLD", "energization": "HOLD",
    }
    write_json(ROOT/"results/kinematic_validation.json", summary)
    write_json(ROOT/"results/motion_samples.json", {"frame": "F0", "nominal": asdict(nominal), "samples": motion})
    print(json.dumps({"cases": len(cases), "all_cases_passed": summary["all_cases_passed"],
                      "max_fd_error_mm_s": max(x["maximum_velocity_fd_error_mm_s"] for x in cases)}, indent=2))


if __name__ == "__main__":
    main()
