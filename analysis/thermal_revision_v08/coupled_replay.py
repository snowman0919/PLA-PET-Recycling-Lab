"""Numerical plant connected to compiled heater components; never equipment."""
import math
import numpy as np
from analysis.thermal_revision_v08.model import ASSUMPTIONS, network, positive
from analysis.thermal_revision_v08.power_loop import PowerLoop


def run_case(base, supports, zones, library, *, contact=200.0, air=8.0,
             support=0.05, sensor_tau_s=0.0, dt=0.05, dx=0.0025,
             duration=1800.0, control_period_s=0.05, extrusion=False,
             chain_open_s=None, sensor_nan_s=None, permit_off_s=None):
    positive(sensor_tau_s, 'sensor time constant', zero=True)
    for value, label in ((dt, 'time step'), (duration, 'duration'),
                         (control_period_s, 'control period')):
        positive(value, label)
    if base['heater_zone_power_w']+[base['die_heater_power_w']] != [100, 100, 100, 60]:
        raise ValueError('plant power must match the compiled allocator watts')
    props = dict(ASSUMPTIONS)
    x, widths, capacity, conductance, area, sink, sensors, contact_areas = network(
        base, supports, zones, contact, air, support, dx, props)
    steps = round(duration/dt)
    control_stride = round(control_period_s/dt)
    if steps < 1 or control_stride < 1 or abs(steps*dt-duration)>1e-8 or abs(control_stride*dt-control_period_s)>1e-8:
        raise ValueError('time grid must preserve fixed control updates')
    n = len(x); ambient = props['ambient_c']
    targets = np.asarray(base['pet_zone_c']+[base['pet_die_c']], dtype=float)
    temp = np.full(n+4, ambient); peak = temp.copy()
    lagged = np.full(4, ambient); sampled = lagged.copy()
    inverse = np.linalg.inv(np.diag(capacity/dt)+conductance+np.diag(sink))
    rated = np.array([100.0, 100.0, 100.0, 60.0])
    on = np.zeros(4); duty = [0.0]*4
    heat_in = loss_total = residual = max_command_w = 0.0
    first_fault_sample = None
    first_target = first_fault = None; fault_bits = 0; after_fault_peak_w = 0.0
    tail_error = 0.0; trace = []
    denied_peak_w = 0.0
    for value in (chain_open_s, sensor_nan_s, permit_off_s):
        if value is not None:
            positive(value, "event time", zero=True)
    with PowerLoop(library) as controller:
        if not np.allclose(targets, controller.targets, atol=1e-6, rtol=0):
            raise ValueError('CAD targets differ from compiled PET firmware profile')
        sample_s = controller.sample_ms/1000.0
        sample_stride = round(sample_s/dt)
        if sample_stride < 1 or abs(sample_stride*dt-sample_s)>1e-8:
            raise ValueError('time grid must preserve firmware sensor sampling')
        for step in range(steps):
            now = step*dt
            actual = sensors@temp
            if step % sample_stride == 0:
                sampled = lagged.copy()
                if sensor_nan_s is not None and now >= sensor_nan_s:
                    sampled[3] = float('nan')
            if step % control_stride == 0:
                duty, enabled = controller.step(sampled, targets, max(1, round(now*1000)),
                    extrusion=extrusion, chain=chain_open_s is None or now < chain_open_s,
                    permit=permit_off_s is None or now < permit_off_s)
                on = np.asarray(enabled, dtype=float); fault_bits = controller.faults
                if fault_bits and first_fault is None:
                    first_fault = now
                    first_fault_sample = dict(zone=controller.fault_zone,
                        sampled_c=[float(v) if math.isfinite(v) else None for v in sampled],
                        invalid_channels=[i for i,v in enumerate(sampled) if not math.isfinite(v)],
                        actual_c=actual.tolist(), targets_c=targets.tolist())
            commanded = float(rated@on)
            max_command_w = max(max_command_w, commanded)
            if first_fault is not None:
                after_fault_peak_w = max(after_fault_peak_w, commanded)
            denied = (chain_open_s is not None and now >= chain_open_s) or (permit_off_s is not None and now >= permit_off_s)
            if denied:
                denied_peak_w = max(denied_peak_w, commanded)
            power = np.r_[np.zeros(n), rated*on]
            radiation = props['emissivity']*5.670374419e-8*area*((temp+273.15)**4-(ambient+273.15)**4)
            updated = inverse@(capacity/dt*temp+sink*ambient+power-radiation)
            loss = float(sum(radiation+sink*(updated-ambient)))
            residual = max(residual, abs(float(sum(capacity*(updated-temp)))-dt*(commanded-loss)))
            heat_in += dt*commanded; loss_total += dt*loss
            temp = updated; peak = np.maximum(peak, temp)
            if not np.isfinite(temp).all() or min(temp) < ambient-1e-6:
                raise ValueError('unstable or nonphysical thermal state')
            sensor_value = sensors@temp
            lagged = sensor_value if sensor_tau_s == 0 else actual+(lagged-actual)*math.exp(-dt/sensor_tau_s)
            error = float(max(abs(sensor_value-targets)))
            if first_target is None and error <= 5:
                first_target = now+dt
            if now+dt >= max(0.0, duration-60.0):
                tail_error = max(tail_error, error)
            if (step+1)%max(1, round(5/dt))==0 or step==steps-1:
                trace.append(dict(time_s=now+dt, sensors_c=sensor_value.tolist(),
                    heater_c=temp[n:n+3].tolist(), duty_percent=duty,
                    commanded_power_w=commanded, fault_bits=fault_bits))
        phase_cap = controller.cap(extrusion)
    stored = float(sum(capacity*(temp-ambient)))
    energy_error = abs(stored-(heat_in-loss_total))
    checks = dict(energy_balance=energy_error < 1e-4, step_energy_balance=residual < 1e-6,
                  phase_power_cap=max_command_w <= phase_cap+1e-6,
                  no_power_after_latched_fault=after_fault_peak_w == 0,
                  no_power_without_permission=denied_peak_w == 0)
    return dict(status='NUMERICAL_REPLAY_PASS' if all(checks.values()) else 'FAIL',
        checks=checks, contact_h_w_m2k=contact, air_h_w_m2k=air, support_g_w_k=support,
        sensor_tau_s=sensor_tau_s, time_step_s=dt, mesh_mm=float(max(widths)*1000),
        control_period_s=control_period_s, sensor_sample_period_s=sample_s,
        duration_s=duration, phase='EXTRUSION' if extrusion else 'PREHEATING',
        barrel_peak_c=float(max(peak[:n])), heater_peaks_c=peak[n:n+3].tolist(),
        die_peak_c=float(peak[-1]), final_sensor_c=(sensors@temp).tolist(),
        time_to_target_band_s=first_target, final_minute_max_error_c=tail_error,
        process_targets_held=(first_fault is None and duration>=60 and tail_error<=5),
        first_fault_s=first_fault, first_fault_sample=first_fault_sample, fault_bits=fault_bits, maximum_power_w=max_command_w,
        after_fault_peak_power_w=after_fault_peak_w, after_permission_loss_power_w=denied_peak_w,
        fault_injection=dict(chain_open_s=chain_open_s, sensor_nan_s=sensor_nan_s, permit_off_s=permit_off_s),
        energy_input_j=heat_in,
        global_energy_residual_j=energy_error, max_step_energy_residual_j=residual,
        contact_areas_m2=contact_areas, trace=trace,
        physical_validation_state='NOT_RUN', fabrication_authorized=False,
        energization_authorized=False, machine_release='HOLD')
