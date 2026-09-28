"""C2 deterministic engineering study. Numerical assumptions are not test evidence."""
from __future__ import annotations
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any
import numpy as np
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class S2:
    candidate_id: str
    tip_mm: float = 110.0
    width_mm: float = 40.0
    eccentric_mm: float = 7.0
    gap_mm: float = 0.8
    hook_depth_mm: float = 12.0
    hooks: int = 8
    ratio_denominator: int = 8
    orbit_rpm: float = 116.0
    screen_hole_mm: float = 4.0
    screen_thickness_mm: float = 2.0
    screen_arc_deg: float = 100.0
    rising_fraction: float = 0.72
    shear_ratio: float = 3.0

    def __post_init__(self):
        if min(self.tip_mm, self.width_mm, self.eccentric_mm, self.gap_mm,
               self.hook_depth_mm, self.orbit_rpm, self.shear_ratio) <= 0:
            raise ValueError("Nonpositive geometry or speed")
        if self.hooks < 3 or self.ratio_denominator < 2:
            raise ValueError("Invalid integer mechanism")
        if not 0.45 <= self.rising_fraction <= 0.9:
            raise ValueError("Unsupported hook family")

    @property
    def chamber_mm(self):
        return self.tip_mm + 2 * (self.eccentric_mm + self.gap_mm)


def hook_polygon(c: S2, samples_per_hook: int = 24) -> np.ndarray:
    """Six polar controls per hook; linear interpolation is manufacturable, not optimal.
    The sharp polyline is for a replaceable test profile; tip radius/finish remain DFM.
    """
    f = c.rising_fraction
    controls = np.array([[0, 0], [0.22, 0.12], [f-0.16, 0.72],
                         [f, 1.0], [f+0.05, 0.88], [1, 0]])
    # Include controls explicitly so the actual tip is not missed by sampling.
    u = np.unique(np.r_[np.linspace(0, 1, samples_per_hook, endpoint=False), controls[:-1, 0]])
    frac = np.interp(u, controls[:, 0], controls[:, 1])
    radius = c.tip_mm/2 - c.hook_depth_mm + c.hook_depth_mm*frac
    angle = 2*np.pi*(np.arange(c.hooks)[:, None] + u[None, :])/c.hooks
    return np.c_[np.ravel(radius[None, :]*np.cos(angle)),
                 np.ravel(radius[None, :]*np.sin(angle))]


def transform(points: np.ndarray, theta: float, c: S2) -> np.ndarray:
    phi = -theta/c.ratio_denominator
    R = np.array([[math.cos(phi), -math.sin(phi)], [math.sin(phi), math.cos(phi)]])
    return points @ R.T + c.eccentric_mm*np.array([math.cos(theta), math.sin(theta)])


def point_jacobian(point: np.ndarray, theta: float, c: S2) -> np.ndarray:
    rotated=transform(np.asarray(point).reshape(1,2),theta,c)[0]-c.eccentric_mm*np.array([math.cos(theta),math.sin(theta)])
    return (c.eccentric_mm*np.array([-math.sin(theta),math.cos(theta)])-
            np.array([-rotated[1],rotated[0]])/c.ratio_denominator)/1000


def generalized_torque(force_N: np.ndarray, point_mm: np.ndarray, theta: float, c: S2) -> float:
    return float(np.asarray(force_N)@point_jacobian(point_mm,theta,c))


def polygon_area(p: np.ndarray) -> float:
    return abs(float(np.sum(p[:, 0]*np.roll(p[:, 1], -1)-p[:, 1]*np.roll(p[:, 0], -1))))/2


def packaging(c: S2) -> dict[str, Any]:
    # Nominal bearing boundary options, not procurement-approved MPNs.
    nominal_bearings = [(35, 62, 14), (40, 68, 15), (45, 75, 16), (50, 80, 16)]
    shaft_radius, min_sleeve_wall, min_root_web = 6.0, 3.0, 3.0
    needed_bore = 2*(shaft_radius+c.eccentric_mm+min_sleeve_wall)
    options = [b for b in nominal_bearings if b[0] >= needed_bore]
    b = options[0] if options else None
    root_radius = c.tip_mm/2-c.hook_depth_mm
    web = root_radius-b[1]/2 if b else -1.0
    # This is a CONSERVATIVE screening rule for the C1 analytic offset family.
    # e*N/R <= 1/1.1 avoids the unoffset curve's zero-derivative cusp regime;
    # it does NOT establish an undercut-free roller offset or contact capacity.
    q = c.ratio_denominator
    pin_radius = max(60.0, 1.1*c.eccentric_mm*(q+1),
                     (16.0+2.0)/(2*math.sin(math.pi/(q+1))))
    pin_plate_od = 2*(pin_radius+8.0+5.0)
    reasons = []
    if not 125 <= c.chamber_mm <= 155:
        reasons.append("CHAMBER_OUTSIDE_HANDOVER_RANGE")
    if b is None or web < min_root_web:
        reasons.append("ECCENTRIC_SLEEVE_OR_BEARING_ROOT_WEB")
    return dict(chamber_mm=c.chamber_mm, min_eccentric_sleeve_od_mm=needed_bore,
                nominal_bearing=b, root_web_mm=web,
                pin_pitch_radius_screen_mm=pin_radius,
                pin_plate_od_screen_mm=pin_plate_od,
                compact_pin_family_possible=pin_plate_od <= 178,
                compact_pin_limit_mm=178,
                kinematic_geometry_feasible=not reasons,
                reject_reasons=reasons,
                mechanism_status="PROFILE_CONTACT_CHECK_REQUIRED" if pin_plate_od <= 178
                else "ALTERNATIVE_CONSTRAINT_REQUIRED_OR_LARGER_CASSETTE",
                bearing_status="NOMINAL_BOUNDARY_NOT_APPROVED_MPN")


def kinematics(c: S2, steps_per_orbit: int = 96) -> dict[str, Any]:
    p = hook_polygon(c)
    minimum = math.inf
    max_speed = 0.0
    screen_near = 0
    total = 0
    q = c.ratio_denominator
    # q complete orbits close every labeled material point, not just identical hooks.
    theta = np.linspace(0, 2*np.pi*q, steps_per_orbit*q+1)
    omega = c.orbit_rpm*2*np.pi/60
    screen_half = math.radians(c.screen_arc_deg/2)
    for t in theta:
        moved = transform(p, float(t), c)
        radial = np.linalg.norm(moved, axis=1)
        minimum = min(minimum, c.chamber_mm/2-float(radial.max()))
        rotated = moved-c.eccentric_mm*np.array([math.cos(t), math.sin(t)])
        v = c.eccentric_mm*np.array([-math.sin(t), math.cos(t)])-np.c_[-rotated[:, 1], rotated[:, 0]]/q
        max_speed = max(max_speed, float(np.linalg.norm(v, axis=1).max())*omega)
        # Pure geometric proximity, not capture probability or particle residence.
        a = np.arctan2(moved[:, 1], moved[:, 0])
        angle_to_bottom = np.arctan2(np.sin(a+np.pi/2), np.cos(a+np.pi/2))
        screen_near += int(np.sum((np.abs(angle_to_bottom) <= screen_half) &
                                  (c.chamber_mm/2-radial <= 5.5)))
        total += len(p)
    return dict(sampled_min_wall_gap_mm=minimum,
                analytical_outer_envelope_gap_mm=c.gap_mm,
                max_profile_point_speed_mm_s=max_speed,
                close_to_screen_geometric_fraction=screen_near/total,
                chamber_free_volume_mL=(np.pi*(c.chamber_mm/2)**2-polygon_area(p))*c.width_mm/1000,
                full_labeled_cycle_orbits=q,
                sampled_positions=len(theta), profile_vertices=len(p),
                closure_error_mm=float(np.max(np.linalg.norm(transform(p, float(theta[-1]), c)-transform(p, 0, c), axis=1))),
                self_rpm=-c.orbit_rpm/q,
                s1_rpm=c.orbit_rpm/c.shear_ratio,
                result_evidence="DETERMINISTIC_KINEMATICS_NOT_BREAKAGE",
                yield_target_mass_fraction=None, throughput_g_h=None,
                jam_probability=None, cutting_torque_Nm=None)


def design_set(n: int = 256) -> list[S2]:
    a = qmc.LatinHypercube(d=13, seed=20260921).random(n)
    rows = [S2("C1-SEED", shear_ratio=116/21.75)]
    for i, u in enumerate(a):
        rows.append(S2(f"C2-{i+1:03d}", tip_mm=90+25*u[0], width_mm=35+10*u[1],
                       eccentric_mm=7+7*u[2], gap_mm=.2+u[3], hook_depth_mm=8+6*u[4],
                       hooks=6+min(4, int(u[5]*5)), ratio_denominator=6+min(10, int(u[6]*11)),
                       orbit_rpm=60+120*u[7], screen_hole_mm=3+2.5*u[8],
                       screen_thickness_mm=2+2*u[9], screen_arc_deg=80+50*u[10],
                       rising_fraction=.62+.18*u[11],
                       shear_ratio=(3.0, 4.0, 16/3)[min(2, int(u[12]*3))]))
    return rows


def diverse_selection(candidates: list[dict], count: int = 48) -> list[str]:
    rows = [r for r in candidates if r["packaging"]["kinematic_geometry_feasible"]]
    fields = ["tip_mm", "eccentric_mm", "gap_mm", "hook_depth_mm", "hooks",
              "ratio_denominator", "orbit_rpm", "screen_hole_mm", "width_mm"]
    X = np.array([[r["design"][f] for f in fields] for r in rows])
    X = (X-X.min(axis=0))/np.maximum(np.ptp(X, axis=0), 1e-9)
    selected = [next((i for i,r in enumerate(rows) if r['design']['candidate_id']=='C1-SEED'),0)]
    d = np.full(len(rows), np.inf)
    while len(selected) < min(count, len(rows)):
        d = np.minimum(d, np.linalg.norm(X-X[selected[-1]], axis=1))
        d[selected] = -1
        selected.append(int(np.argmax(d)))
    return [rows[i]["design"]["candidate_id"] for i in selected]


@dataclass(frozen=True)
class Thermal:
    material: str = "PLA"
    ambient_C: float = 25
    inlet_C: float = 25
    chamber_heat_W: float = 30
    heat_to_polymer_fraction: float = .35
    chamber_UA_W_K: float = 2
    polymer_metal_G_W_K: float = 2
    metal_shell_G_W_K: float = 8
    hotend_G_W_K: float = .005
    hotend_C: float = 230
    polymer_mass_kg: float = .04
    metal_heat_capacity_J_K: float = 700
    shell_heat_capacity_J_K: float = 540
    mass_flow_g_h: float = 100
    cp_J_kg_K: float = 1800
    natural_UA_W_K: float = .3
    fan_factor: float = 1
    motor_loss_W: float = 0
    gear_loss_W: float = 0
    motor_heat_capacity_J_K: float = 350
    gear_heat_capacity_J_K: float = 500
    motor_UA_W_K: float = 1.5
    gear_UA_W_K: float = 1
    motor_gear_G_W_K: float = .6
    gear_shell_G_W_K: float = .15

    def __post_init__(self):
        if self.material not in {"PLA", "PET", "TPU"}:
            raise ValueError("Unsupported material; PET is not PETG")
        if min(self.chamber_UA_W_K,self.polymer_metal_G_W_K,self.metal_shell_G_W_K,
               self.polymer_mass_kg,self.metal_heat_capacity_J_K,self.shell_heat_capacity_J_K,self.cp_J_kg_K,
               self.natural_UA_W_K,self.motor_heat_capacity_J_K,self.gear_heat_capacity_J_K,
               self.motor_UA_W_K,self.gear_UA_W_K,self.motor_gear_G_W_K,self.gear_shell_G_W_K) <= 0:
            raise ValueError("Thermal coefficients must be positive")
        if (not 0 <= self.heat_to_polymer_fraction <= 1 or self.chamber_heat_W < 0
                or self.motor_loss_W < 0 or self.gear_loss_W < 0
                or self.mass_flow_g_h < 0 or not 0 <= self.fan_factor <= 1
                or self.natural_UA_W_K > self.chamber_UA_W_K):
            raise ValueError("Invalid heat source")


def thermal_matrix(c: Thermal):
    gp, gm, ua, gh = c.polymer_metal_G_W_K,c.metal_shell_G_W_K,c.chamber_UA_W_K,c.hotend_G_W_K
    ua = c.natural_UA_W_K+c.fan_factor*(ua-c.natural_UA_W_K)
    mg, gs = c.motor_gear_G_W_K,c.gear_shell_G_W_K
    flow = c.mass_flow_g_h/3.6e6*c.cp_J_kg_K
    C = np.array([c.polymer_mass_kg*c.cp_J_kg_K,c.metal_heat_capacity_J_K,c.shell_heat_capacity_J_K,
                  c.motor_heat_capacity_J_K,c.gear_heat_capacity_J_K])
    K = np.array([[gp+flow,-gp,0,0,0],
                  [-gp,gp+gm,-gm,0,0],
                  [0,-gm,gm+ua+gh+gs,0,-gs],
                  [0,0,0,c.motor_UA_W_K+mg,-mg],
                  [0,0,-gs,-mg,c.gear_UA_W_K+mg+gs]])
    b = np.array([c.chamber_heat_W*c.heat_to_polymer_fraction+flow*c.inlet_C,
                  c.chamber_heat_W*(1-c.heat_to_polymer_fraction), ua*c.ambient_C+gh*c.hotend_C,
                  c.motor_loss_W+c.motor_UA_W_K*c.ambient_C,
                  c.gear_loss_W+c.gear_UA_W_K*c.ambient_C])
    return C,K,b


def thermal_run(c: Thermal, duration_s: float = 3600, dt_s: float = 1,
                initial_C: list[float] | None = None):
    if dt_s <= 0 or duration_s <= 0:
        raise ValueError("Positive integration interval required")
    C,K,b = thermal_matrix(c)
    n = math.ceil(duration_s/dt_s)
    dt = duration_s/n
    A = np.diag(C/dt)+K
    inv = np.linalg.inv(A)
    T = np.full(5,c.ambient_C,dtype=float) if initial_C is None else np.asarray(initial_C,dtype=float)
    if T.shape != (5,) or not np.all(np.isfinite(T)):
        raise ValueError("initial_C must contain five finite node temperatures")
    initial_E = float(C@T)
    net_E = 0.0
    max_balance = 0.0
    trace = []
    for j in range(n):
        old = T.copy()
        T = inv @ (C/dt*T+b)
        input_minus_output = float(np.sum(b-K@T))
        net_E += dt*input_minus_output
        max_balance = max(max_balance, abs(float(C@(T-old))/dt-input_minus_output))
        if j%max(1,round(30/dt)) == 0 or j == n-1:
            trace.append([round((j+1)*dt,8),*T.tolist()])
    return dict(parameters=asdict(c), final_polymer_C=float(T[0]), final_metal_C=float(T[1]),
                final_shell_C=float(T[2]), final_motor_C=float(T[3]), final_gear_C=float(T[4]),
                final_state_C=T.tolist(), steady_C=np.linalg.solve(K,b).tolist(),
                energy_balance_residual_J=float(C@T)-initial_E-net_E,
                max_step_power_residual_W=max_balance,
                trace_columns=["time_s","polymer_C","metal_C","shell_C","motor_C","gear_C"],trace=trace,
                evidence="UNCALIBRATED_LUMPED_NETWORK_SENSITIVITY",
                excluded=["local_flash_temperature","fracture_heat_partition_calibration","dust_flow",
                          "nonlinear_temperature_dependent_properties","measured_fan_curve",
                          "selected_motor_and_gear_thermal_parameters"])


def thermal_duty_run(c: Thermal, segments: list[dict], dt_s: float = 1):
    """Carry thermal state through batch/fan-fault segments; still uncalibrated."""
    if not segments:
        raise ValueError("At least one duty segment is required")
    allowed={"chamber_heat_W","mass_flow_g_h","fan_factor","motor_loss_W","gear_loss_W","inlet_C"}
    state=None
    elapsed=0.0
    peaks=np.full(5,-np.inf)
    records=[]
    energy_residual=0.0
    for segment in segments:
        duration=float(segment.get("duration_s",0))
        values={k:v for k,v in segment.items() if k in allowed}
        unknown=set(segment)-allowed-{"name","duration_s"}
        if duration <= 0 or unknown:
            raise ValueError(f"Invalid duty segment: {sorted(unknown)}")
        cfg=replace(c,**values)
        run=thermal_run(cfg,duration,dt_s,state)
        state=np.asarray(run["final_state_C"])
        peaks=np.maximum(peaks,state)
        elapsed+=duration
        energy_residual+=run["energy_balance_residual_J"]
        records.append(dict(name=segment.get("name",f"segment_{len(records)+1}"),end_time_s=elapsed,
                            fan_factor=cfg.fan_factor,chamber_heat_W=cfg.chamber_heat_W,
                            motor_loss_W=cfg.motor_loss_W,gear_loss_W=cfg.gear_loss_W,
                            final_state_C=state.tolist()))
    return dict(node_order=["polymer","shear_metal","shell_spreader","motor_case","gear_case"],
                segments=records,peak_node_C=peaks.tolist(),final_state_C=state.tolist(),
                energy_balance_residual_J=energy_residual,
                evidence="UNCALIBRATED_DUTY_AND_FAN_FAULT_SENSITIVITY_NOT_HARDWARE_TEST")


def thermal_capacities_from_cad(cad: dict) -> dict:
    """Lower-bound heat capacities from generated C2 metal volumes, not measured masses."""
    records={r["part_id"]:r for r in cad["records"]}
    steel_ids=("C1_SCREEN_REFERENCE","C1_LEFT_WEAR_SHELL","C2_RIGHT_WEAR_SHELL_1",
               "C2_RIGHT_WEAR_SHELL_2","C2_FIXED_SHEAR")
    aluminium_ids=("C2_THERMAL_SADDLE_L","C2_SADDLE_CAP_L","C2_THERMAL_SADDLE_R","C2_SADDLE_CAP_R")
    def volume(ids):
        return sum(records[x]["volume_mm3"]*records[x]["quantity"] for x in ids)
    steel_volume=volume(steel_ids)
    aluminium_volume=volume(aluminium_ids)
    return dict(shear_metal_J_K=steel_volume*7.85e-6*500,
                shell_spreader_J_K=aluminium_volume*2.70e-6*900,
                steel_volume_mm3=steel_volume,aluminium_volume_mm3=aluminium_volume,
                steel_part_ids=list(steel_ids),aluminium_part_ids=list(aluminium_ids),
                assumptions={"steel_density_kg_mm3":7.85e-6,"steel_cp_J_kg_K":500,
                             "aluminium_density_kg_mm3":2.70e-6,"aluminium_cp_J_kg_K":900},
                status="CAD_VOLUME_DERIVED_ASSUMED_DENSITY_CP_NOT_MEASURED_MASS")


def equivalent_motor_load(s1_torque_Nm: float, s2_torque_Nm: float,
                          s1_rpm: float, s2_rpm: float, motor_rpm: float,
                          eta1: float = .75, eta2: float = .80):
    if not 0 < eta1 <= 1 or not 0 < eta2 <= 1 or motor_rpm <= 0:
        raise ValueError("Invalid efficiency or speed")
    p1 = s1_torque_Nm*s1_rpm*2*np.pi/60
    p2 = s2_torque_Nm*s2_rpm*2*np.pi/60
    p = p1/eta1+p2/eta2
    return dict(s1_output_W=p1,s2_output_W=p2,motor_shaft_required_W=p,
                motor_required_Nm=p/(motor_rpm*2*np.pi/60),
                required_total_ratio_s1=motor_rpm/s1_rpm,
                required_total_ratio_s2=motor_rpm/s2_rpm,
                efficiency_status="ASSUMED_COMPLETE_PATH_EFFICIENCIES_NOT_MEASURED")


def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=True,default=lambda v: v.item() if isinstance(v,np.generic) else v.tolist())+"\n")


def main():
    rows = []
    for c in design_set():
        pack = packaging(c)
        rows.append(dict(design=asdict(c),packaging=pack,
                         kinematics=kinematics(c) if pack['kinematic_geometry_feasible'] else None))
    ids = diverse_selection(rows)
    write_json(ROOT/'results/s2_candidates.json',rows)
    flat=[]
    for r in rows:
        flat.append({**r['design'],**{k:v for k,v in r['packaging'].items() if not isinstance(v,(list,dict,tuple))},
                     'reject_reasons':'|'.join(r['packaging']['reject_reasons']),
                     'sampled_gap_mm':r['kinematics']['sampled_min_wall_gap_mm'] if r['kinematics'] else None})
    with (ROOT/'results/s2_candidates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    jobs=[]
    for cid in ids:
        for material in ['PLA','PET','TPU']:
            jobs.append(dict(job_id=f'{cid}-{material}',candidate_id=cid,material=material,
                             status='BLOCKED_CALIBRATION_NOT_RUN',material_grade=None,material_lot=None,
                             calibration_id=None,feed_distribution_id=None,replicate_seed=20260921,
                             outputs={k:None for k in ['target_yield_mass_fraction','throughput_g_h','peak_torque_Nm',
                             'rms_torque_Nm','jam_probability','specific_energy_J_g','max_polymer_C']},
                             evidence_type=None,raw_data_sha256=None))
    write_json(ROOT/'experiments/dem_job_manifest.json',jobs)
    thermal=[]
    for material,cp in [('PLA',1800),('PET',1200),('TPU',1700)]:
        for amb in [25,35]:
            for heat in [10,30,60]:
                for ua in [.5,2,4]:
                    for coupling in [.005,.10]:
                        cfg=Thermal(material=material,cp_J_kg_K=cp,ambient_C=amb,inlet_C=amb,
                                    chamber_heat_W=heat,chamber_UA_W_K=ua,hotend_G_W_K=coupling)
                        r=thermal_run(cfg)
                        thermal.append({k:v for k,v in r.items() if k not in ['trace','trace_columns']})
    write_json(ROOT/'results/thermal_sweep.json',thermal)
    example=thermal_run(Thermal())
    write_json(ROOT/'results/thermal_reference_trace.json',example)
    motors=[]
    for rpm in [3000]:
        for s1t,s2t,label in [(10,1,'LOW_ASSUMPTION'),(18,3,'WORKING_ASSUMPTION'),(25,5,'HIGH_ASSUMPTION')]:
            for s1rpm,s2rpm in [(20,60),(40,120),(60,180)]:
                motors.append(dict(label=label,ratio_policy='EACH_SPEED_PAIR_REQUIRES_DIFFERENT_GEARING_AT_3000_RPM; NOT_PWM_ONLY',s1_torque_Nm=s1t,s2_torque_Nm=s2t,s1_rpm=s1rpm,
                                   s2_rpm=s2rpm,**equivalent_motor_load(s1t,s2t,s1rpm,s2rpm,rpm)))
    write_json(ROOT/'results/motor_load_envelope.json',motors)
    valid=[r for r in rows if r['packaging']['kinematic_geometry_feasible']]
    summary=dict(revision='C2.0',base_commit='0aa312c5be0ce566bc06f63fa4fdd5c9e7f3f47e',
                 handover_file_count_verified=41,candidates=len(rows),lhs_new_candidates=len(rows)-1,
                 geometrically_feasible=len(valid),rejected=len(rows)-len(valid),
                 compact_pin_precheck_possible=sum(r['packaging']['compact_pin_family_possible'] for r in valid),
                 alternative_constraint_or_larger_pin_cassette=len(valid)-sum(r['packaging']['compact_pin_family_possible'] for r in valid),
                 diverse_dem_designs=len(ids),material_specific_dem_jobs=len(jobs),
                 actual_dem_runs=0,actual_physical_tests=0,performance_models_trained=0,
                 thermal_scenarios=len(thermal),thermal_material_properties='ASSUMED_NOT_GRADE_CALIBRATED',
                 max_thermal_energy_residual_J=max(abs(r['energy_balance_residual_J']) for r in thermal),
                 c1_geometry_role='SEED_NOT_OPTIMUM',motor_status='UNSELECTED',
                 budget_status='INCOMPLETE_COSTS_NOT_A_FEASIBLE_QUOTE',
                 fabrication='HOLD',energization='HOLD',procurement='HOLD')
    write_json(ROOT/'results/summary.json',summary)
    print(json.dumps(summary,indent=2,default=lambda v: v.item()))

if __name__=='__main__':
    main()
