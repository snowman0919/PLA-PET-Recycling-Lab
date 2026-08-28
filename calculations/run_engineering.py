#!/usr/bin/env python3
"""v0.4 coherent flow, torque, power, cooling and control calculations."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/"cad/parameters/baseline.json").read_text())
REV="solid-manifold-openmodelica-v0.4"


def throughput_model():
    d=P["extruder"]["selected_diameter_mm"]/1000
    depth=P["extruder"]["feed_depth_ratio"]*d
    pitch=P["extruder"]["pitch_ratio"]*d
    displacement=math.pi*d*depth*pitch
    materials={
        "PLA":{"bulk_density":[240,280,320],"fill":[0.22,0.30,0.34],"efficiency":[0.55,0.68,0.76],"melt_factor":[0.76,0.88,0.94]},
        "PET":{"bulk_density":[210,250,300],"fill":[0.20,0.30,0.34],"efficiency":[0.52,0.68,0.74],"melt_factor":[0.72,0.86,0.92]},
    }
    rpms=[10,14,18,20,24,28,32,36]
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
    return {"model":"solid_conveying_displacement_x_bulk_density_x_fill_x_efficiency_x_melt_backflow_factor","displacement_m3_rev":displacement,"radial_clearance_mm_range":[0.14,0.16],"pressure_backflow_and_tip_leakage_in_melt_factor":True,"rows":rows,"profile_points":profiles,"physical_status":"PHYSICAL_NOT_RUN"}


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
        for gph in (50,100,150,200):
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
    return {"values":values,"torque_reference_plane":"cutter-shaft equivalent","strict_order_pass":passed,"relief_location":"physical DRV-F01 at motor side, upstream of chain and phase gears","motor_side_relief_settings_nm":s["motor_side_relief_settings_nm_at_efficiency_0_85"],"phase_tangential_force_n":round(peak/r_phase,1),"phase_separating_force_n":round(peak/r_phase*math.tan(math.radians(20)),1),"chain_tight_side_increment_n":round(peak/r_sprocket,1),"tip_force_n":round(peak/(s["cutter_od_mm"]/2000),1),"status":"DIGITAL_SCREENING_PHYSICAL_NOT_RUN"}


def drive_thresholds():
    c=P["shredder"]["motor"]["reference_calibration"]
    thresholds={}
    for material,limits in P["shredder"]["material_torque_limits_nm"].items():
        def amps(torque): return c["no_load_current_a"]+torque/(c["torque_per_amp_nm"]*c["motor_to_cutter_ratio"]*c["drivetrain_efficiency"])
        thresholds[material]={"continuous_torque_nm":limits["continuous"],"jam_torque_nm":limits["jam"],"reference_continuous_current_a":round(amps(limits["continuous"]),2),"reference_jam_current_a":round(amps(limits["jam"]),2),"release_status":"REFERENCE_ONLY_RECALCULATE_AFTER_DONOR_CALIBRATION"}
    return {"calibration":c,"thresholds":thresholds,"hardcoded_universal_current_limit":False}


def diameter_control(delay_s):
    dt=.1; queue=[0.0]*max(1,int(delay_s/dt)); diameter=1.75; puller=1.; integral=0.; errors=[]
    for i in range(int(900/dt)):
        disturbance=.025 if 2500<=i<4300 else (-.018 if 6000<=i<7200 else 0.)
        delayed=queue.pop(0); queue.append(puller-1); diameter+=dt*((1.75+disturbance-.42*delayed)-diameter)/6
        error=diameter-1.75; integral=max(-.08,min(.08,integral+error*dt)); puller=max(.88,min(1.12,1+.40*error+.025*integral)); errors.append(error)
    return {"model":"first_order_plus_transport_delay","delay_s":delay_s,"rms_error_mm":round(math.sqrt(sum(e*e for e in errors)/len(errors)),4),"max_abs_error_mm":round(max(map(abs,errors)),4),"status":"VIRTUAL_ONLY"}


def main():
    if P["revision"]!=REV: raise SystemExit("revision mismatch")
    flow=throughput_model(); candidates=screw_candidates(); cooling=cooling_matrix(); hierarchy=torque_hierarchy(); drive=drive_thresholds()
    power=P["power"]|{"calculated_concurrent_peak_w":sum(P["power"][k] for k in ("heater_peak_w","shredder_peak_w","extruder_peak_w","motion_fans_logic_peak_w")),"arbiter_margin_w":P["power"]["psu_rating_w"]-P["power"]["arbiter_peak_w"]}
    area=math.pi*(.00175**2)/4; speed=(.2/3600)/(1240*area); delay=(P["forming"]["die_to_gauge_mm"]/1000)/speed
    summary={"revision":REV,"release_class":P["release_class"],"throughput":flow,"screw_candidates":candidates,"cooling":cooling,"torque_hierarchy":hierarchy,"drive_calibration":drive,"diameter_loop":diameter_control(delay),"power":power,"thermal":{"hot_path_design_c":300,"shield_screen_c":52,"polymer_keepout_c":42,"status":"DIGITAL_SCREENING_PHYSICAL_NOT_RUN"},"pet_predry":"UNQUALIFIED_EXTERNAL_PROCESS"}
    out=ROOT/"simulation"; out.mkdir(exist_ok=True); (out/"engineering_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    with (ROOT/"calculations/throughput_rpm_sensitivity.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=flow["rows"][0].keys(),lineterminator="\n"); w.writeheader(); w.writerows(flow["rows"])
    with (ROOT/"calculations/cooling_matrix.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cooling[0].keys(),lineterminator="\n"); w.writeheader(); w.writerows(cooling)
    lines=["# 16 mm × 16 L/D screw — RPM/처리량 sensitivity","","`m_dot = channel displacement × bulk density × fill × conveying efficiency × (1-backflow-leakage) × RPM`이며 radial clearance 0.14–0.16 mm, pressure backflow와 flight-tip leakage를 melt factor에 포함했다. 실제 feed/melt 시험은 `PHYSICAL_NOT_RUN`이다.","","|재질|RPM|low|nominal|high|residence s|","|---|---:|---:|---:|---:|---:|"]
    for r in flow["rows"]: lines.append(f"|{r['material']}|{r['rpm']}|{r['throughput_low_gph']}|{r['throughput_nominal_gph']}|{r['throughput_high_gph']}|{r['residence_low_s']}–{r['residence_high_s']}|")
    lines += ["",f"PLA profile 18 rpm nominal {flow['profile_points']['PLA']['throughput_nominal_gph']} g/h, PET profile 20 rpm nominal {flow['profile_points']['PET']['throughput_nominal_gph']} g/h다. 200 g/h는 선택 범위 14–28 rpm의 nominal prediction으로 지지되지 않으며 optimistic fill corner 또는 32–36 rpm 검증이 필요한 stretch target이다."]
    (ROOT/"calculations/screw_sensitivity.md").write_text("\n".join(lines)+"\n")
    (ROOT/"calculations/shredder_drive_and_cutter.md").write_text(f"""# Cycloidal-derived cutter와 interchangeable drive

CUT-01은 7 hook, pitch의 76% cycloidal capture rise와 24% fast relief를 쓰는 비대칭 profile이다. Actuator는 특정 MY1016Z/coupling에 종속되지 않고 DRV-01 slotted plate, donor-specific DRV-Axx, motor-side DRV-F01, #35 chain과 cutter-side DRV-02 hub를 사용한다.

토크 계층 `14 < 18 < 22 < 34 < 48 N·m`는 모두 cutter-shaft equivalent다. DRV-F01의 실제 motor-side setting은 12:18/24/30에서 각각 17.25/12.94/10.35 N·m이며 digital check는 `{hierarchy['strict_order_pass']}`다. Cutter-equivalent 22 N·m에서 cutter tip {hierarchy['tip_force_n']} N, phase tangential/separating {hierarchy['phase_tangential_force_n']}/{hierarchy['phase_separating_force_n']} N, chain tight-side increment {hierarchy['chain_tight_side_increment_n']} N이다. DRV-02와 phase key는 sacrificial element가 아니다.

Current threshold는 donor calibration 뒤 `I = I0 + T/(Kt × ratio × efficiency)`로 계산한다. 현재 reference sensitivity는 실제 donor 합격값이 아니며 universal 16/18 A limit를 release하지 않는다. Gate-1 및 donor calibration은 `PHYSICAL_NOT_RUN`이다.
""")
    (ROOT/"calculations/thermal_power_forming.md").write_text(f"""# 열·전력·forming screening

24 V 600 W PSU에서 동시 peak 합은 {power['calculated_concurrent_peak_w']} W이므로 허용하지 않는다. Hardware/state arbiter는 {power['arbiter_peak_w']} W, margin {power['arbiter_margin_w']} W이며 shredder와 heater/screw는 상호배제한다.

`cooling_matrix.csv`는 PLA/PET, 50/100/150/200 g/h, fan 40/70/100%, duct 2.0/3.5/5.0 m/s를 모두 계산한다. 200 g/h에서 요구 h가 실측되지 않았으므로 risk가 남는 조합은 virtual requirement이며 puller-entry thermocouple 없이는 합격이 아니다.

PET predry는 `UNQUALIFIED_EXTERNAL_PROCESS`; 65 °C/7 h를 qualified recipe로 주장하지 않는다.
""")
    (ROOT/"calculations/engineering_report.md").write_text(f"""# 공학 계산 통합 보고 — {REV}

- release: `DIGITAL_FABRICATION_BASELINE`, `PHYSICAL_VALIDATION_PENDING`
- envelope: 470 × 700 × 930 mm
- screw profiles: PLA 18 rpm / PET 20 rpm; nominal {flow['profile_points']['PLA']['throughput_nominal_gph']}/{flow['profile_points']['PET']['throughput_nominal_gph']} g/h
- 200 g/h: nominal 미입증 stretch target
- torque hierarchy: 14 < 18 < 22 < 34 < 48 N·m, PASS
- 24 V power arbiter: {power['arbiter_peak_w']} W < 600 W, PASS
- physical cutter/feed/melt/cooling/dimension tests: `PHYSICAL_NOT_RUN`

OpenModelica dynamic peak는 `simulation/openmodelica/results/summary.json`에서 구조 load case로 전달하며, 해석은 실제 chip size·wear·melt quality를 증명하지 않는다.
""")
    print("ENGINEERING_CALCULATIONS_OK")


if __name__=="__main__": main()
