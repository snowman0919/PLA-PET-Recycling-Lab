"""Bind conditional demand to exact catalogue variants and complete option prices."""
from pathlib import Path
import csv,hashlib,json,math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
KGF_CM=0.0980665
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def output(torque,rpm,ratio=1.0,eta=1.0):
    if not all(math.isfinite(x) and x>0 for x in (torque,rpm,ratio,eta)) or ratio<1 or eta>1:raise ValueError('Invalid drive point')
    return {'rpm':rpm/ratio,'torque_nm':torque*ratio*eta,'shaft_power_w':torque*rpm*math.pi/30*eta}
def conservative_catalog_nm(top_nm,kgfcm):return min(top_nm,kgfcm*KGF_CM)
def main():
    study=json.loads((HERE/'results.json').read_text())
    if study['status']!='CONDITIONAL_DEMAND_SIZING':raise ValueError('Wrong study')
    rows=study['cases'];rec=[r for r in rows if 'recommended' in r['case']]
    required_sh=max(r['closed_form']['shred_peak_nm'] for r in rec)
    required_ex=max(r['screw_peak_nm'] for r in rec)
    html=(HERE/'source_cache/GGM_SHOP.html').read_text()
    if not all(s in html for s in ('53,840','K9G75C (1/75) (+47,410','K9G150C (1/150) (+47,410','165,000')):raise ValueError('Option-price evidence missing')
    options=[('SH-GGM75','GGM K9DG60N2 + K9G75C',conservative_catalog_nm(9.41,94.1),40,2.5,.85,'shredder'),('EX-GGM150','GGM K9DG60N2 + K9G150C',conservative_catalog_nm(10,100),20,1,1,'extruder')]
    selected=[]
    for key,model,torque,rpm,ratio,eta,axis in options:
        point=output(torque,rpm,ratio,eta);need=required_sh if axis=='shredder' else required_ex
        selected.append({'id':key,'axis':axis,'model':model,'voltage_v':24,'motor_rated_output_w_before_gear':60,'motor_rated_current_a':4.6,'gearbox_rated_torque_nm_used':torque,'gearbox_rated_rpm':rpm,'gearbox_max_torque_nm_used':100*KGF_CM,'external_ratio':ratio,'external_efficiency_assumption':eta,'output':point,'required_scope_peak_nm':need,'matches_declared_demand_torque':point['torque_nm']>=need,'motor_base_krw':53840,'gear_option_krw':47410,'unit_total_krw_vat_included':101250,'quantity':1,'motor_plus_gear_mass_kg':3.24,'source_id':'GGM_SHOP'})
    if not all(s['matches_declared_demand_torque'] for s in selected):raise ValueError('Selected motor below declared demand')
    alternatives=[{'model':'ZENG 42GP-775 24V 120rpm selected screenshot','output':output(20*KGF_CM,100,2.5,.85),'decision':'BELOW_RECOMMENDED','price':'Screenshot USD30.21; wrong option for recommendation; not current checkout'}, {'model':'ZENG 32GP-31ZY 24V 57rpm selected screenshot','output':output(19*KGF_CM,46,3,.85),'decision':'BELOW_RECOMMENDED','price':'Screenshot USD16.82; wrong option for recommendation; not current checkout'}, {'model':'TT GMP60-60127-2460 ratio47 with existing2.5 chain','output':output(100*KGF_CM,70,2.5,.85),'decision':'SHREDDER_HEADROOM_REFERENCE_NOT_PURCHASED','price':'EXACT_SINGLE_UNIT_QUOTE_REQUIRED','source_id':'TT_GMP60'}]
    tiers=[]
    for tier,rate,sh_spec,sh_rpm,ex_spec,ex_rpm in [('minimum',50,7,10,4,10),('recommended',100,15,16,9.5,20),('headroom',150,20,24,15,30)]:
        included=[r for r in rows if r['case'].endswith('_'+tier)]
        tiers.append({'tier':tier,'nominal_feed_map_target_gph':rate,'scope':'Conditional input envelope, not guaranteed throughput or absolute material minimum','shredder_rated_torque_selection_nm':sh_spec,'shredder_rated_speed_reference_rpm':sh_rpm,'extruder_rated_torque_selection_nm':ex_spec,'extruder_rated_speed_reference_rpm':ex_rpm,'model_shred_peak_nm':max(r['closed_form']['shred_peak_nm'] for r in included),'model_extruder_peak_nm':max(r['screw_peak_nm'] for r in included)})
    legacy_22_motor=22/(2.5*.85)
    limits={'shredder_legacy_22nm_fuse_at_gearbox_nm':legacy_22_motor,'selected_gearbox_limit_nm':100*KGF_CM,'legacy_fuse_reuse_allowed':False,'reason':'22 Nm cutter equivalent exceeds the selected gearbox published100kgf.cm limit; current limit and sacrificial element must be recalibrated before hardware use','extruder_legacy_22nm_trip_reuse_allowed':False,'new_trip_current_a':None,'hardware_settings_written':False,'peak_stall_current_a':'NOT_SUPPLIED_BY_SELECTED_CATALOGUE','unidentified_controllers':'EXCLUDED_FROM_BASELINE','BTS7960_available_count':2,'additional_driver_purchase':0}
    report={'status':'SELECTED_DIGITAL_REFERENCE_PENDING_INTERFACE_AND_PURCHASE_REVIEW','selected':selected,'specification_tiers':tiers,'alternatives':alternatives,'protection_integration':limits,'recommended_case_uncertainty':'Separate viscosity1.5x, shear50MPa and pressure-work efficiency0.3 cases; not simultaneous all-corner qualification','joint_high_viscosity_and_low_efficiency_screen_peak_nm':required_ex+3.946326*(.4/.3-1),'joint_corner_covered_by_selected_extruder':False,'total_motor_and_gear_price_krw':202500,'standard_shipping_by_displayed_threshold_krw':0,'shipping_final_checkout':'NOT_VERIFIED','optional_bracket_each_krw':15180,'bracket_selected':False,'lowest_global_price_claim':False,'purchase_performed':False,'power_integration':{'psu_reported_w':800,'retained_control_cap_w':500,'motor_rated_electrical_input_w':24*4.6,'auxiliary_envelope_w':45,'heater_power_budget_w_before_driver_loss':500-24*4.6-45,'full_360w_heat_plus_rated_motor_exceeds_500w':True,'action':'retain phase arbitration; recalculate allocator reservations; no unconditional full-power simultaneous run'},'motor_mount_cad_finalized':False,'firmware_calibrated':False,'physical_validation':'NOT_RUN','machine_release':'HOLD','source_sha256':{p.name:sha(p) for p in (HERE/'results.json',HERE/'sources.json',Path(__file__))}}
    (HERE/'motor_selection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with (HERE/'motor_shortlist.csv').open('w',newline='') as f:
        fields=['id','model','voltage_v','gearbox_rated_rpm','gearbox_rated_torque_nm_used','external_ratio','output_rpm','output_torque_nm','unit_total_krw_vat_included','quantity','source_id']
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator=chr(10));writer.writeheader()
        for s in selected:writer.writerow({k:(s['output']['rpm'] if k=='output_rpm' else s['output']['torque_nm'] if k=='output_torque_nm' else s[k]) for k in fields})
    print(json.dumps({'status':report['status'],'recommended_peak_nm':[required_sh,required_ex],'selected_outputs':[s['output'] for s in selected],'pair_price_krw':202500}))
if __name__=='__main__':main()
