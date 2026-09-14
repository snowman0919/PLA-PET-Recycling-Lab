"""Conservative 1D finite volumes; numerical verification is not qualification."""
import json
import math
from pathlib import Path
import numpy as np

INPUTS = Path(__file__).with_name('model_inputs.json')
ASSUMPTIONS = json.loads(INPUTS.read_text())


def positive(value, label, zero=False):
    if isinstance(value, bool) or not math.isfinite(value) or (value < 0 if zero else value <= 0):
        raise ValueError('invalid '+label)
    return float(value)


def network(base, supports_m, zones, contact_h, air_h, support_g, dx, props):
    length = positive(props['barrel_length_mm'], 'length')/1000
    od, bore = base['barrel_od_mm']/1000, base['barrel_id_mm']/1000
    if not 0 < bore < od or not 0 < dx <= length/4:
        raise ValueError('invalid barrel section or mesh')
    if len(supports_m) != 2 or not 0 < supports_m[0] < supports_m[1] < length:
        raise ValueError('invalid support stations')
    for value, name in ((contact_h,'contact'),(air_h,'convection'),(support_g,'support')):
        positive(value,name,zero=True)
    if len(zones) != 3 or any(not 0 <= a < b <= length*1000 for a,b in zones):
        raise ValueError('invalid heater coverage')
    if any(zones[i][1] > zones[i+1][0] for i in (0,1)):
        raise ValueError('overlapping heater zones')
    n = math.ceil(length/dx)
    edges = np.linspace(0,length,n+1); widths = np.diff(edges)
    x = (edges[1:]+edges[:-1])/2
    section = math.pi*(od**2-bore**2)/4
    cap = np.r_[props['steel_density_kg_m3']*props['steel_cp_j_kg_k']*section*widths,
                np.full(3,props['heater_capacity_j_k']),props['die_capacity_j_k']]
    if not np.isfinite(cap).all() or min(cap) <= 0:
        raise ValueError('invalid heat capacities')
    conductance = np.zeros((n+4,n+4))
    surface = np.r_[math.pi*od*widths,np.zeros(3),props['die_surface_m2']]
    def link(i,j,g):
        conductance[i,i] += g; conductance[j,j] += g
        conductance[i,j] -= g; conductance[j,i] -= g
    k = positive(props['steel_k_w_m_k'],'conductivity')
    for i in range(n-1): link(i,i+1,k*section/(x[i+1]-x[i]))
    circumference = math.pi*od-props['closure_gap_mm']/1000
    positive(circumference,'contact circumference')
    areas = []
    for j,(start,stop) in enumerate(zones):
        cap[n+j] = props['heater_capacity_j_k']*(stop-start)/45.0
        overlap = np.maximum(0,np.minimum(edges[1:],stop/1000)-np.maximum(edges[:-1],start/1000))
        area = overlap*circumference; areas.append(float(sum(area)))
        for i in np.flatnonzero(area): link(i,n+j,contact_h*area[i])
        surface[:n] -= area
        surface[n+j] = math.pi*(od+0.004)*(stop-start)/1000
    link(n-1,n+3,positive(props['die_contact_g_w_k'],'die contact',zero=True))
    if min(surface)<-1e-12: raise ValueError('negative exposed surface')
    sink = air_h*surface
    support_width = positive(props['support_width_mm'],'support width')/1000
    for station in supports_m:
        overlap = np.maximum(0,np.minimum(edges[1:],station+support_width/2)-np.maximum(edges[:-1],station-support_width/2))
        if abs(sum(overlap)-support_width)>1e-10:
            raise ValueError('support footprint outside barrel')
        sink[:n] += support_g*overlap/support_width
    sensors = np.zeros((4,n+4))
    for j,station_mm in enumerate(base['barrel_sensor_bores_mm']):
        station = station_mm/1000
        if not x[0] <= station <= x[-1]: raise ValueError('sensor outside mesh')
        hi = min(max(int(np.searchsorted(x,station)),1),n-1); lo=hi-1
        fraction = (station-x[lo])/(x[hi]-x[lo])
        sensors[j,lo] = 1-fraction; sensors[j,hi] = fraction
    sensors[3,-1] = 1
    if not np.allclose(conductance.sum(axis=0),0,atol=1e-9):
        raise ValueError('internal heat links do not conserve energy')
    return x,widths,cap,conductance,surface,sink,sensors,areas


def thermal_screen(base,supports_m,zones,contact_h,air_h,support_g,dt=0.5,
                   dx=0.0025,duration=1800.0,mode='relay',overrides=None):
    props = dict(ASSUMPTIONS); props.update(overrides or {})
    positive(dt,'time step'); positive(duration,'duration')
    steps = round(duration/dt)
    if steps<1 or abs(steps*dt-duration)>1e-8: raise ValueError('incomplete time interval')
    if mode not in {'relay','constant'}: raise ValueError('unknown excitation')
    x,widths,cap,g,surface,sink,sensors,areas = network(
        base,supports_m,zones,contact_h,air_h,support_g,dx,props)
    n = len(x); ambient = props['ambient_c']
    if not math.isfinite(ambient) or ambient<=-273.15: raise ValueError('invalid ambient')
    epsilon = props['emissivity']
    if not math.isfinite(epsilon) or not 0<=epsilon<=1: raise ValueError('invalid emissivity')
    inverse = np.linalg.inv(np.diag(cap/dt)+g+np.diag(sink))
    temp = np.full(n+4,ambient); peak=temp.copy(); on=np.ones(4,dtype=bool)
    targets = np.asarray(base['pet_zone_c']+[base['pet_die_c']],dtype=float)
    powers = np.asarray(base['heater_zone_power_w']+[base['die_heater_power_w']],dtype=float)
    if len(powers)!=4 or not np.isfinite(powers).all() or min(powers)<0:
        raise ValueError('invalid heater power')
    if not np.isfinite(targets).all(): raise ValueError('invalid targets')
    residual=0.0; input_j=0.0; loss_j=0.0; first_target=None; trace=[]
    for step in range(steps):
        measured=sensors@temp
        if mode=='relay':
            on[measured<targets-1]=True; on[measured>targets+1]=False
        power=np.r_[np.zeros(n),powers*on]
        radiation=epsilon*5.670374419e-8*surface*((temp+273.15)**4-(ambient+273.15)**4)
        updated=inverse@(cap/dt*temp+sink*ambient+power-radiation)
        loss=float(sum(radiation+sink*(updated-ambient)))
        imbalance=float(sum(cap*(updated-temp))-dt*(sum(power)-loss))
        residual=max(residual,abs(imbalance)); input_j+=dt*sum(power); loss_j+=dt*loss
        temp=updated; peak=np.maximum(peak,temp)
        if not np.isfinite(temp).all() or min(temp)<ambient-1e-6:
            raise ValueError('nonphysical temperature or unstable explicit radiation')
        if first_target is None and all(sensors@temp>=targets-5): first_target=(step+1)*dt
        if step==steps-1 or (step+1)%max(1,round(30/dt))==0:
            trace.append({'time_s':(step+1)*dt,'sensors_c':(sensors@temp).tolist(),
                          'heater_c':temp[n:n+3].tolist(),'barrel_max_c':float(max(temp[:n]))})
    stored_j=float(sum(cap*(temp-ambient)))
    return {'contact_h_w_m2_k':contact_h,'air_h_w_m2_k':air_h,
            'support_conductance_w_k':support_g,'timestep_s':dt,'mesh_mm':1000*max(widths),
            'duration_s':duration,'mode':mode,'barrel_peak_c':float(max(peak[:n])),
            'heater_peaks_c':peak[n:n+3].tolist(),'feed_end_peak_c':float(peak[0]),
            'die_peak_c':float(peak[-1]),'final_sensor_c':(sensors@temp).tolist(),
            'time_to_target_band_s':first_target,'heat_input_j':float(input_j),
            'heat_loss_j':loss_j,'stored_heat_j':stored_j,
            'max_step_energy_residual_j':residual,
            'global_energy_residual_j':float(stored_j-(input_j-loss_j)),
            'contact_areas_m2':areas,'trace':trace,
            'axial_positions_mm':(1000*x).tolist(),'final_barrel_c':temp[:n].tolist(),
            'peak_barrel_c':peak[:n].tolist(),
            'peak_free_growth_mm':float(props['alpha_per_k']*sum((peak[:n]-ambient)*widths)*1000),
            'growth_scope':'integral of pointwise temporal maxima: upper screen, not simultaneous field',
            'physical_validation_state':'NOT_RUN','fabrication_authorized':False}


def metric_vector(record):
    return np.array([record['barrel_peak_c'],record['die_peak_c'],
                     *record['heater_peaks_c'],*record['final_sensor_c']])


def refinement_error(coarse,fine):
    return float(max(abs(metric_vector(coarse)-metric_vector(fine))))
