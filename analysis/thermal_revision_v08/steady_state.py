"""Inverse steady heat balance; identify infeasible demand before tuning controls."""
import numpy as np
from analysis.thermal_revision_v08.model import ASSUMPTIONS, network


def required_power(base, supports, zones, *, contact=200.0, air=8.0,
                   support=0.05, dx=0.0025, overrides=None):
    props = dict(ASSUMPTIONS); props.update(overrides or {})
    x, widths, capacity, g, area, sink, sensors, areas = network(
        base, supports, zones, contact, air, support, dx, props)
    ambient = float(props['ambient_c'])
    targets = np.asarray(base['pet_zone_c']+[base['pet_die_c']], dtype=float)
    if targets.shape != (4,) or not np.isfinite(targets).all():
        raise ValueError('four finite target temperatures required')
    if not -273.15 < ambient <= min(targets):
        raise ValueError('targets must not be below ambient')
    n, count = len(x), len(capacity)
    input_matrix = np.zeros((count,4)); input_matrix[n:,:] = np.eye(4)
    epsilon = float(props['emissivity'])
    if not 0 <= epsilon <= 1:
        raise ValueError('invalid emissivity')
    factor = epsilon*5.670374419e-8*area
    temp = np.full(count, float(np.mean(targets)))
    watts = np.array(base['heater_zone_power_w']+[base['die_heater_power_w']], dtype=float)
    def balance(t, q):
        radiation = factor*((t+273.15)**4-(ambient+273.15)**4)
        return np.r_[g@t+sink*(t-ambient)+radiation-input_matrix@q, sensors@t-targets]
    for iteration in range(60):
        residual = balance(temp, watts)
        error = float(np.linalg.norm(residual, ord=np.inf))
        if error < 1e-8:
            break
        jacobian = np.block([[g+np.diag(sink+4*factor*(temp+273.15)**3), -input_matrix],
                             [sensors, np.zeros((4,4))]])
        delta = np.linalg.solve(jacobian, -residual)
        scale = 1.0
        while scale >= 2**-20:
            trial_t, trial_q = temp+scale*delta[:count], watts+scale*delta[count:]
            if (np.isfinite(trial_t).all() and min(trial_t) > -273.15
                    and np.linalg.norm(balance(trial_t,trial_q),ord=np.inf) < error):
                temp, watts = trial_t, trial_q
                break
            scale /= 2
        else:
            raise ValueError('steady thermal solve failed to reduce residual')
    else:
        raise ValueError('steady thermal solve did not converge')
    residual = balance(temp,watts)
    rated = np.asarray(base['heater_zone_power_w']+[base['die_heater_power_w']])
    radiation = factor*((temp+273.15)**4-(ambient+273.15)**4)
    feasible = bool(np.all(watts >= -1e-7) and np.all(watts <= rated+1e-7))
    return dict(required_watts=watts.tolist(), rated_watts=rated.tolist(),
        sensors_c=(sensors@temp).tolist(), heater_c=temp[n:n+3].tolist(),
        die_c=float(temp[-1]), barrel_peak_c=float(max(temp[:n])),
        local_residual_w=float(max(abs(residual[:count]))),
        sensor_residual_c=float(max(abs(residual[count:]))),
        global_residual_w=float(sum(watts)-sum(sink*(temp-ambient)+radiation)),
        heating_only_feasible=feasible, iterations=iteration,
        physical_validation_state='NOT_RUN', energization_authorized=False)
