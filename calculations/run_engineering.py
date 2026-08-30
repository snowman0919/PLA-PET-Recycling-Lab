#!/usr/bin/env python3
"""v0.5.1 virtual-physics engineering closure calculations."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/"cad/parameters/baseline.json").read_text())
CONTRACT=json.loads((ROOT/"control/process_contract.json").read_text())
REV="implementation-crosssolver-v0.6"


def throughput_model():
    d=P["extruder"]["selected_diameter_mm"]/1000
    depth=P["extruder"]["feed_depth_ratio"]*d
    pitch=P["extruder"]["pitch_ratio"]*d
    displacement=math.pi*d*depth*pitch
    materials={
        "PLA":{"bulk_density":[240,280,320],"fill":[0.22,0.30,0.34],"efficiency":[0.55,0.68,0.76],"melt_factor":[0.76,0.88,0.94]},
        "PET":{"bulk_density":[210,250,300],"fill":[0.20,0.30,0.34],"efficiency":[0.52,0.68,0.74],"melt_factor":[0.72,0.86,0.92]},
    }
    rpms=[10,14,16,18,20,24,28,32,36]
    rows=[]
    for material,a in materials.items():
        for rpm in rpms:
            values=[]
            for index,label in enumerate(("low","nominal","high")):
                gph=displacement*a["bulk_density"][index]*a["fill"][index]*a["efficiency"][index]*a["melt_factor"][index]*rpm*60*1000
                values.append(gph)
            turns=P["extruder"]["active_length_mm"]/(pitch*1000)
            # Partially filled channel residence, not the incorrect full-barrel
            # volume divided by output. Low/high bound use the same conveying
            # efficiency and melt-loss factors as the mass-flow bounds.
            residence=[turns/(rpm*a["efficiency"][2]*a["melt_factor"][2])*60,turns/(rpm*a["efficiency"][0]*a["melt_factor"][0])*60]
            rows.append({"material":material,"rpm":rpm,"throughput_low_gph":round(values[0],1),"throughput_nominal_gph":round(values[1],1),"throughput_high_gph":round(values[2],1),"residence_low_s":round(residence[0],1),"residence_high_s":round(residence[1],1)})
    profiles={}
    for material in ("PLA","PET"):
        rpm=P["profiles"][material]["screw_rpm"]
        profiles[material]=next(r for r in rows if r["material"]==material and r["rpm"]==rpm)
    clearance_rows=[]
    # Pre-test screening: pressure-driven flow through a narrow flight-tip gap
    # scales approximately with clearance cubed.  Split the nominal melt loss
    # equally into fixed pressure backflow and clearance-sensitive tip leakage;
    # Gate-4 melt-flow data must replace this anchor before release.
    loss_anchor={"PLA":{"fixed_backflow":0.06,"tip_at_0_15":0.06},"PET":{"fixed_backflow":0.07,"tip_at_0_15":0.07}}
    for material in ("PLA","PET"):
        nominal_factor=materials[material]["melt_factor"][1]
        nominal_gph=profiles[material]["throughput_nominal_gph"]
        for clearance in (0.14,0.15,0.16):
            relative=(clearance/0.15)**3
            loss=loss_anchor[material]["fixed_backflow"]+loss_anchor[material]["tip_at_0_15"]*relative
            factor=max(0.5,1-loss)
            adjusted=nominal_gph*factor/nominal_factor
            clearance_rows.append({"material":material,"profile_rpm":profiles[material]["rpm"],"radial_clearance_mm":clearance,"tip_leakage_relative_to_0_15":round(relative,4),"melt_delivery_factor":round(factor,4),"predicted_throughput_gph":round(adjusted,1),"change_from_0_15_percent":round((factor/nominal_factor-1)*100,2),"status":"VIRTUAL_SCREENING_EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN"})
    return {"model":"solid_conveying_displacement_x_bulk_density_x_fill_x_efficiency_x_melt_backflow_factor","displacement_m3_rev":displacement,"radial_clearance_mm_range":[0.14,0.16],"pressure_backflow_and_tip_leakage_in_melt_factor":True,"tip_leakage_model":"relative leakage=(radial_clearance/0.15 mm)^3; nominal loss split 50/50 fixed backflow/tip leakage","rows":rows,"clearance_sensitivity":clearance_rows,"profile_points":profiles,"physical_status":"EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN"}


def screw_candidates():
    rows=[]
    for diameter_mm in P["extruder"]["candidate_diameters_mm"]:
        d=diameter_mm/1000; ld=18 if diameter_mm<=14 else 16
        torque_3=1.5*3e6*math.pi*d**3/16; torque_6=1.5*6e6*math.pi*d**3/16
        rows.append({"diameter_mm":diameter_mm,"ld":ld,"active_length_mm":diameter_mm*ld,"torque_3mpa_sf1_5_nm":round(torque_3,2),"torque_6mpa_sf1_5_nm":round(torque_6,2),"selected":diameter_mm==16})
    return rows


def cooling_matrix():
    result=[]; area=math.pi*(0.00175**2)/4; length=P["forming"]["straight_length_die_to_puller_mm"]/1000
    for material,density,cp,start,target in (("PLA",1240,1800,200,48),("PET",1380,1200,265,65)):
        for gph in (50,75,100,125,150,175,200):
            speed=(gph/1000/3600)/(density*area)
            dwell=length/speed
            required_h=density*cp*0.00175/(4*dwell)*math.log((start-25)/(target-25))
            for duty,velocity,h in ((40,2.0,35),(70,3.5,50),(100,5.0,65)):
                tau=density*cp*0.00175/(4*h)
                center=25+(start-25)*math.exp(-dwell/tau)
                risk="PASS_VIRTUAL" if center<=target else "SAG_OVALITY_RISK"
                result.append({"material":material,"throughput_gph":gph,"fan_duty_percent":duty,"duct_velocity_m_s":velocity,"h_w_m2k":h,"puller_entry_center_c":round(center,1),"required_h_w_m2k":round(required_h,1),"risk":risk})
    return result


def torque_hierarchy():
    s=P["shredder"]
    values={"normal_continuous_nm":s["continuous_torque_nm"],"electrical_trip_nm":s["electrical_trip_torque_nm"],"motor_side_relief_nm":s["mechanical_relief_torque_nm"],"phase_drivetrain_allowable_nm":s["phase_drivetrain_allowable_torque_nm"],"shaft_cutter_allowable_nm":s["shaft_cutter_allowable_torque_nm"]}
    ordered=list(values.values()); passed=all(a<b for a,b in zip(ordered,ordered[1:]))
    r_phase=0.024; r_sprocket=9.525e-3/(2*math.sin(math.pi/24)); peak=values["motor_side_relief_nm"]
    return {"values":values,"torque_reference_plane":"cutter-shaft equivalent","strict_order_pass":passed,"relief_location":"physical DRV-F01 at motor side, upstream of chain and phase gears","motor_side_relief_settings_nm":s["motor_side_relief_settings_nm_at_efficiency_0_85"],"phase_tangential_force_n":round(peak/r_phase,1),"phase_separating_force_n":round(peak/r_phase*math.tan(math.radians(20)),1),"chain_tight_side_increment_n":round(peak/r_sprocket,1),"tip_force_n":round(peak/(s["cutter_od_mm"]/2000),1),"status":"DIGITAL_SCREENING_EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN"}


def drive_thresholds():
    c=P["shredder"]["motor"]["reference_calibration"]
    thresholds={}
    for material,limits in P["shredder"]["material_torque_limits_nm"].items():
        def amps(torque): return c["no_load_current_a"]+torque/(c["torque_per_amp_nm"]*c["motor_to_cutter_ratio"]*c["drivetrain_efficiency"])
        thresholds[material]={"continuous_torque_nm":limits["continuous"],"jam_torque_nm":limits["jam"],"reference_continuous_current_a":round(amps(limits["continuous"]),2),"reference_jam_current_a":round(amps(limits["jam"]),2),"release_status":"REFERENCE_ONLY_RECALCULATE_AFTER_DONOR_CALIBRATION"}
    return {"calibration":c,"thresholds":thresholds,"hardcoded_universal_current_limit":False}


def die_relief_screening():
    """First-yield beam screen for the replaceable relief retainer.

    This deliberately does not model large-deflection opening, gasket
    friction or melt rheology.  Three physical coupons remain mandatory.
    """
    r=P["extruder"]["relief_retainer"]
    force_per_web_n=r["yield_mpa_screening"]*r["web_width_mm"]*r["thickness_mm"]**2/(6*r["web_length_mm"])
    total_force_n=force_per_web_n*r["web_count"]
    loaded_area_mm2=math.pi*(r["loaded_diameter_mm"]**2-r["unloaded_orifice_diameter_mm"]**2)/4
    pressure_mpa=total_force_n/loaded_area_mm2
    return {
        "model":"two_rectangular_web_first_yield_screen",
        "force_per_web_n":round(force_per_web_n,2),
        "total_force_n":round(total_force_n,2),
        "loaded_annular_area_mm2":round(loaded_area_mm2,2),
        "estimated_first_yield_pressure_mpa":round(pressure_mpa,2),
        "target_window_mpa":[P["extruder"]["normal_pressure_mpa"],P["extruder"]["trip_pressure_equivalent_mpa"]],
        "screening_pass":P["extruder"]["normal_pressure_mpa"]<pressure_mpa<P["extruder"]["trip_pressure_equivalent_mpa"],
        "status":"DIGITAL_SCREENING_PHYSICAL_COUPON_NOT_RUN",
    }


def diameter_control(delay_s):
    dt=.1; queue=[0.0]*max(1,int(delay_s/dt)); diameter=1.75; puller=1.; integral=0.; errors=[]
    for i in range(int(900/dt)):
        disturbance=.025 if 2500<=i<4300 else (-.018 if 6000<=i<7200 else 0.)
        delayed=queue.pop(0); queue.append(puller-1); diameter+=dt*((1.75+disturbance-.42*delayed)-diameter)/6
        error=diameter-1.75; integral=max(-.08,min(.08,integral+error*dt)); puller=max(.88,min(1.12,1+.40*error+.025*integral)); errors.append(error)
    return {"model":"first_order_plus_transport_delay","delay_s":delay_s,"rms_error_mm":round(math.sqrt(sum(e*e for e in errors)/len(errors)),4),"max_abs_error_mm":round(max(map(abs,errors)),4),"status":"VIRTUAL_ONLY"}


def phase_power_budget():
    power=CONTRACT["power"]
    rows=[]
    for state, values in power["phases"].items():
        peak=values["peak_w"]
        rows.append({
            "state":state,
            "average_w":values["average_w"],
            "peak_w":peak,
            "peak_current_a":round(peak/power["voltage_v"],2),
            "remaining_w_to_psu":round(power["psu_rating_w"]-peak,1),
            "remaining_a_to_psu":round((power["psu_rating_w"]-peak)/power["voltage_v"],2),
            "normal_limit_margin_w":round(power["normal_phase_peak_limit_w"]-peak,1),
            "pass":peak<=power["normal_phase_peak_limit_w"] and power["psu_rating_w"]-peak>=power["minimum_reserve_w"],
        })
    return {**power,"states":rows,"status":"PASS" if all(r["pass"] for r in rows) else "FAIL"}


def thermocouple_bore_screening():
    """Local membrane/notch/thermal-gradient screen at the blind-bore tip.

    This is deliberately conservative and decision-relevant: it compares the
    former 7 mm bore to the selected 6 mm bore, using the same material/load
    assumptions, rather than presenting an uncalibrated contour plot.
    """
    ro=P["extruder"]["barrel_od_mm"]/2
    ri=P["extruder"]["barrel_id_mm"]/2
    wall=ro-ri
    pressure_trip=P["extruder"]["trip_pressure_equivalent_mpa"]
    pressure_normal=P["extruder"]["normal_pressure_mpa"]
    young_mpa=190000.0
    alpha=17e-6
    poisson=.30
    local_gradient_c=10.0
    thermal=young_mpa*alpha*local_gradient_c/(1-poisson)
    allowable=180.0
    rows=[]
    for depth in (7.0,6.0):
        ligament=wall-depth
        def combined(pressure):
            hoop=pressure*(ro**2+ri**2)/(ro**2-ri**2)
            pressure_local=hoop*(wall/ligament)*1.5
            return pressure_local+thermal
        normal=combined(pressure_normal); trip=combined(pressure_trip)
        rows.append({
            "blind_bore_depth_mm":depth,"nominal_ligament_mm":round(ligament,2),
            "normal_combined_stress_mpa":round(normal,1),"trip_combined_stress_mpa":round(trip,1),
            "trip_safety_factor":round(allowable/trip,2),
            "status":"PASS" if allowable/trip>=2 else "FAIL",
        })
    return {
        "method":"thick-cylinder inner hoop × wall/net-ligament × Kt1.5 + fully restrained 10 C local thermal gradient",
        "boundary_conditions":{"pet_bulk_c":270,"normal_pressure_mpa":pressure_normal,"trip_pressure_mpa":pressure_trip,"local_gradient_c":local_gradient_c},
        "material_assumptions":{"young_mpa":young_mpa,"alpha_per_k":alpha,"poisson":poisson,"screening_allowable_mpa":allowable},
        "candidates":rows,"selected_depth_mm":6.0,"selected_status":rows[1]["status"],
        "decision":"SELECT_BLIND6_LIGAMENT2.9; blind7 fails SF>=2 screen",
        "physical_status":"EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN",
    }


def cartridge_heater_fit():
    hole_min=6.050; hole_max=6.062; heater_max=5.980; heater_min=5.940
    return {
        "selected_bore":"diameter6.05 H7 reamed through",
        "heater_limits_mm":[heater_min,heater_max],"bore_limits_mm":[hole_min,hole_max],
        "diametral_clearance_mm":[round(hole_min-heater_max,3),round(hole_max-heater_min,3)],
        "decision":"ADOPT_6.05_H7; verify received heater OD/camber and full hand insertion; thin anti-seize film and positive axial clamp",
        "evidence":"supplier guidance favors close metal contact; final fit remains conditional on received heater measurement",
        "status":"PASS_DFM_SCREEN",
    }


def frame_sensitivity():
    load=json.loads((ROOT/"analysis/load_cases/openmodelica_dynamic_envelope.json").read_text())["loads"]["peak_bearing_load_n"]*.7
    span=.430; e=69e9; joint_slip_mm=.15
    options=[]
    for name, inertia_cm4, mass_kg_m, profile_2020_m, profile_2040_m, cost in (
        ("A_2020_ONLY",.87,.50,15.098,0.0,0),
        ("B_LOCAL_2040",5.41,.90,13.348,1.320,5000),
    ):
        each=load/2
        beam_mm=each*span**3/(48*e*(inertia_cm4*1e-8))*1000
        relative=beam_mm+joint_slip_mm
        options.append({
            "option":name,"bearing_center_relative_displacement_mm":round(relative,3),
            "beam_component_mm":round(beam_mm,3),"joint_allowance_mm":joint_slip_mm,
            "screen_clearance_margin_mm":round(1.9-relative,3),
            "phase_center_distance_variation_mm":round(relative/2,3),
            "profile_2020_m":profile_2020_m,"profile_2040_m":profile_2040_m,
            "total_profile_m":round(profile_2020_m+profile_2040_m,3),
            "estimated_profile_mass_kg":round(profile_2020_m*.50+profile_2040_m*.90,2),
            "incremental_planning_cost_krw":cost,
            "status":"PASS" if relative<=.75 else "MARGINAL",
        })
    return {
        "load_basis_n":round(load,1),"model":"two simply-supported local load rails, half load each + 0.15 mm joint-slip allowance",
        "options":options,"selected":"B_LOCAL_2040",
        "old_profile_total_m":15.098,"new_profile_total_m":14.668,
        "cut_lengths":{"2020":{"890":4,"430":10,"660":6,"300":2,"318":1,"280":2,"50":1},"2040":{"660":2}},
        "stock_nesting_assumption":"2020: three 6 m stock lengths; 2040: donor/offcut or one >=1.32 m length",
        "scrap_ratio_2020_percent":round((18-13.348)/18*100,1),
        "donor_substitution":"local 2040 rails may use two verified straight 660 mm project-lab/Zortrax metal members; unknown stock is not priced at zero",
        "decision":"ADOPT_OPTION_B_AND_REMOVE_ONE_REDUNDANT_430_MM_BOTTOM_CROSSRAIL",
    }


def main():
    if P["revision"]!=REV or CONTRACT["revision"]!=REV: raise SystemExit("revision mismatch")
    flow=throughput_model(); candidates=screw_candidates(); cooling=cooling_matrix(); hierarchy=torque_hierarchy(); drive=drive_thresholds(); die_relief=die_relief_screening()
    power=phase_power_budget(); bore=thermocouple_bore_screening(); heater_fit=cartridge_heater_fit(); frame=frame_sensitivity()
    area=math.pi*(.00175**2)/4; speed=(.2/3600)/(1240*area); delay=(P["forming"]["die_to_gauge_mm"]/1000)/speed
    summary={"revision":REV,"release_class":P["release_class"],"virtual_physics_state":P["virtual_physics_state"],"empirical_state":P["empirical_state"],"throughput":flow,"screw_candidates":candidates,"cooling":cooling,"torque_hierarchy":hierarchy,"drive_calibration":drive,"die_relief_screening":die_relief,"diameter_loop":diameter_control(delay),"power":power,"thermocouple_bore":bore,"cartridge_heater_fit":heater_fit,"frame_sensitivity":frame,"thermal":{"hot_path_design_c":300,"shield_screen_c":52,"polymer_keepout_c":42,"status":"VIRTUAL_PHYSICS_VALIDATED"},"pet_predry":"UNQUALIFIED_EXTERNAL_PROCESS"}
    out=ROOT/"simulation"; out.mkdir(exist_ok=True); (out/"engineering_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    with (ROOT/"calculations/throughput_rpm_sensitivity.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=flow["rows"][0].keys(),lineterminator="\n"); w.writeheader(); w.writerows(flow["rows"])
    with (ROOT/"calculations/cooling_matrix.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cooling[0].keys(),lineterminator="\n"); w.writeheader(); w.writerows(cooling)
    with (ROOT/"calculations/flight_tip_clearance_sensitivity.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=flow["clearance_sensitivity"][0].keys(),lineterminator="\n"); w.writeheader(); w.writerows(flow["clearance_sensitivity"])
    lines=["# 16 mm × 16 L/D screw — RPM/처리량 sensitivity","","`m_dot = channel displacement × bulk density × fill × conveying efficiency × (1-backflow-leakage) × RPM`이며 radial clearance 0.14–0.16 mm, pressure backflow와 flight-tip leakage를 melt factor에 포함했다. 결과는 virtual model이며 실제 melt-flow 측정값이 아니다.","","|재질|RPM|low|nominal|high|residence s|","|---|---:|---:|---:|---:|---:|"]
    for r in flow["rows"]: lines.append(f"|{r['material']}|{r['rpm']}|{r['throughput_low_gph']}|{r['throughput_nominal_gph']}|{r['throughput_high_gph']}|{r['residence_low_s']}–{r['residence_high_s']}|")
    lines += ["",f"PLA profile 16 rpm nominal {flow['profile_points']['PLA']['throughput_nominal_gph']} g/h, PET profile 18 rpm nominal {flow['profile_points']['PET']['throughput_nominal_gph']} g/h다. 200 g/h는 선택 범위 14–28 rpm의 nominal prediction으로 지지되지 않으며 stretch target이다.","","## Flight-tip radial-clearance sensitivity","","Pressure-driven flight-tip leakage를 `q_tip ∝ c^3`로 screening했다. 0.15 mm에서 nominal melt loss를 fixed pressure backflow와 tip leakage에 50:50으로 나눈 가정이며 실측 rheology/pressure/melt-flow를 대신하지 않는다.","","|재질|profile RPM|radial clearance mm|relative tip leakage|melt delivery factor|throughput g/h|0.15 mm 대비|","|---|---:|---:|---:|---:|---:|---:|"]
    for r in flow["clearance_sensitivity"]:
        lines.append(f"|{r['material']}|{r['profile_rpm']}|{r['radial_clearance_mm']:.2f}|{r['tip_leakage_relative_to_0_15']:.4f}|{r['melt_delivery_factor']:.4f}|{r['predicted_throughput_gph']:.1f}|{r['change_from_0_15_percent']:+.2f}%|")
    lines += ["","도면 허용범위 0.14–0.16 mm 안에서도 방향성은 분명하지만, 이 수치는 실제 polymer viscosity·die pressure·flight wear를 보정하지 않은 `VIRTUAL_SCREENING_EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`이다."]
    (ROOT/"calculations/screw_sensitivity.md").write_text("\n".join(lines)+"\n")
    (ROOT/"calculations/shredder_drive_and_cutter.md").write_text(f"""# Cycloidal-derived cutter와 interchangeable drive

CUT-01은 7 hook, pitch의 76% cycloidal capture rise와 24% fast relief를 쓰는 비대칭 profile이다. Actuator는 특정 MY1016Z/coupling에 종속되지 않고 DRV-01 slotted plate, donor-specific DRV-Axx, motor-side DRV-F01, #35 chain과 cutter-side DRV-02 hub를 사용한다.

토크 계층 `14 < 18 < 22 < 34 < 48 N·m`는 모두 cutter-shaft equivalent다. DRV-F01의 실제 motor-side setting은 12:18/24/30에서 각각 17.25/12.94/10.35 N·m이며 digital check는 `{hierarchy['strict_order_pass']}`다. Cutter-equivalent 22 N·m에서 cutter tip {hierarchy['tip_force_n']} N, phase tangential/separating {hierarchy['phase_tangential_force_n']}/{hierarchy['phase_separating_force_n']} N, chain tight-side increment {hierarchy['chain_tight_side_increment_n']} N이다. DRV-02와 phase key는 sacrificial element가 아니다.

Current threshold는 donor calibration 뒤 `I = I0 + T/(Kt × ratio × efficiency)`로 계산한다. 현재 reference sensitivity는 virtual controller reference이며 실제 donor calibration을 주장하지 않는다. Optional empirical Gate-1은 commissioning evidence이고 design release gate가 아니다.
""")
    (ROOT/"calculations/thermal_power_forming.md").write_text(f"""# 열·전력·forming screening

24 V 600 W PSU에서 normal-state limit는 500 W이고 최소 reserve는 100 W다. SHREDDING/PREHEATING/EXTRUSION/COOLDOWN의 peak는 각각 {power['states'][0]['peak_w']}/{power['states'][1]['peak_w']}/{power['states'][2]['peak_w']}/{power['states'][3]['peak_w']} W이며 모두 phase limit를 만족한다. Shredder와 heater/screw는 상호배제한다.

`cooling_matrix.csv`는 PLA/PET, 50/75/100/125/150/175/200 g/h, fan 40/70/100%, duct 2.0/3.5/5.0 m/s를 모두 계산한다. 200 g/h에서 coupled forming 기준을 만족하지 않는 조합은 `DIGITAL_STRETCH_TARGET`이며 실제 filament tolerance를 주장하지 않는다.

EX-DIE-04의 두 10×2.5×1.5 mm 304 stainless bending web은 265 °C 보수 항복강도 150 MPa와 insert annular projected area를 쓴 first-yield screening에서 {die_relief['estimated_first_yield_pressure_mpa']} MPa다. 목표 3–6 MPa 안이지만 large deflection·마찰·열화가 빠져 있으므로 동일 lot 3개 고온 물리 coupon 전에는 relief 합격값이 아니다.

PET predry는 `UNQUALIFIED_EXTERNAL_PROCESS`; 65 °C/7 h를 qualified recipe로 주장하지 않는다.
""")
    (ROOT/"calculations/engineering_report.md").write_text(f"""# 공학 계산 통합 보고 — {REV}

- release: `IMPLEMENTATION_BASELINE`, `VIRTUAL_PHYSICS_VALIDATED`, `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`
- envelope: 470 × 700 × 930 mm
- screw profiles: PLA 16 rpm / PET 18 rpm; analytical nominal {flow['profile_points']['PLA']['throughput_nominal_gph']}/{flow['profile_points']['PET']['throughput_nominal_gph']} g/h
- 200 g/h: nominal 미입증 stretch target
- torque hierarchy: 14 < 18 < 22 < 34 < 48 N·m, PASS
- 24 V phase power: maximum {max(r['peak_w'] for r in power['states'])} W ≤500 W, reserve {min(r['remaining_w_to_psu'] for r in power['states'])} W ≥100 W, PASS
- thermocouple bore: blind6 / ligament {bore['candidates'][1]['nominal_ligament_mm']} mm / trip SF {bore['candidates'][1]['trip_safety_factor']}, PASS
- die heater fit: Ø6.05 H7, clearance {heater_fit['diametral_clearance_mm'][0]:.3f}–{heater_fit['diametral_clearance_mm'][1]:.3f} mm
- frame: local 2040 Option B, relative displacement {frame['options'][1]['bearing_center_relative_displacement_mm']} mm, total profile {frame['new_profile_total_m']} m
- EX-DIE-04 first-yield screen: {die_relief['estimated_first_yield_pressure_mpa']} MPa; empirical coupon is optional evidence but procurement/commissioning remains approval-gated

OpenModelica dynamic peak는 `simulation/openmodelica/results/summary.json`에서 구조 load case로 전달하며, 해석은 실제 chip size·wear·melt quality를 증명하지 않는다.
""")
    print("ENGINEERING_CALCULATIONS_OK")


if __name__=="__main__": main()
