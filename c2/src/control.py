"""Fail-closed control reference. NOT deployable motor/heater firmware."""
from __future__ import annotations
from dataclasses import dataclass
import math

MATERIALS = {
    'PLA': {'derate_C': 40., 'stop_C': 50., 'restart_C': 35.},
    'PET': {'derate_C': 45., 'stop_C': 55., 'restart_C': 40.},
    'TPU': {'derate_C': 40., 'stop_C': 50., 'restart_C': 35.},
}
# Provisional commissioning policies, NOT material-certified safety temperatures.
# Motor/gearbox limits must be populated from the selected drive's qualification.
REQUIRED_SENSORS = ('ambient', 's1_wall', 's2_shear', 's2_screen', 'motor_case', 'gear_case')

@dataclass
class Controller:
    qualified: bool = False
    run_latched: bool = False
    latched_fault: str | None = None
    motor_limit_C: float | None = None
    gear_limit_C: float | None = None
    current_limit_A: float | None = None
    minimum_running_rpm: float | None = None

    def evaluate(self, *, material: str, temperatures: dict[str,float], sensor_age_s: float,
                 estop_closed: bool, guards_closed: bool, fan_ok: bool,
                 jam_detected: bool, start_edge: bool = False, reset_edge: bool = False,
                 run_request: bool = False, buffer_full: bool = False,
                 hardware_overtemp_closed: bool = True,
                 drive_current_A: float | None = None, drive_rpm: float | None = None,
                 drive_sample_age_s: float = 0):
        fault = None
        if not estop_closed or not guards_closed:
            fault = 'SAFETY_CHAIN_OPEN'
        elif not hardware_overtemp_closed:
            fault = 'HARDWARE_OVERTEMP_CHAIN_OPEN'
        elif material not in MATERIALS:
            fault = 'UNKNOWN_MATERIAL'
        elif not math.isfinite(sensor_age_s) or not 0 <= sensor_age_s <= 1.0:
            fault = 'STALE_SENSOR'
        elif any(k not in temperatures or not math.isfinite(temperatures[k]) or
                 not -20 <= temperatures[k] <= 150 for k in REQUIRED_SENSORS):
            fault = 'INVALID_SENSOR'
        elif not fan_ok:
            fault = 'COOLING_FAULT'
        elif jam_detected:
            fault = 'JAM_NO_AUTOMATIC_REVERSE'
        elif run_request and (drive_current_A is None or drive_rpm is None
                              or not math.isfinite(drive_current_A) or drive_current_A < 0
                              or not math.isfinite(drive_rpm) or drive_rpm < 0):
            fault = 'INVALID_DRIVE_FEEDBACK'
        elif run_request and (not math.isfinite(drive_sample_age_s)
                              or not 0 <= drive_sample_age_s <= 1.0):
            fault = 'STALE_DRIVE_FEEDBACK'
        elif (run_request and self.current_limit_A is not None
              and drive_current_A is not None and drive_current_A >= self.current_limit_A):
            fault = 'OVERCURRENT_HARDWARE_LIMIT_REQUIRED'
        elif (run_request and (self.run_latched or start_edge)
              and self.current_limit_A is not None and self.minimum_running_rpm is not None
              and drive_current_A is not None and drive_rpm is not None
              and drive_current_A >= .8*self.current_limit_A
              and drive_rpm < self.minimum_running_rpm):
            fault = 'JAM_NO_AUTOMATIC_REVERSE'
        elif self.motor_limit_C is not None and temperatures['motor_case'] >= self.motor_limit_C:
            fault = 'MOTOR_OVERTEMP'
        elif self.gear_limit_C is not None and temperatures['gear_case'] >= self.gear_limit_C:
            fault = 'GEAR_OVERTEMP'
        elif max(temperatures[k] for k in ('s1_wall','s2_shear','s2_screen')) >= MATERIALS[material]['stop_C']:
            fault = 'CHAMBER_OVERTEMP'
        if fault:
            self.latched_fault = fault
            self.run_latched = False
        cold = material in MATERIALS and all(k in temperatures and math.isfinite(temperatures[k])
                   and temperatures[k] < MATERIALS[material]['restart_C']
                   for k in ('s1_wall','s2_shear','s2_screen'))
        if reset_edge and not fault and cold:
            self.latched_fault = None
            self.run_latched = False
            # A reset never starts either shredder or heater.
            return dict(state='RESET_WAIT_START',m1_fraction=0.,fan_request=True,heat_enable=False)
        if self.latched_fault:
            return dict(state='FAULT',reason=self.latched_fault,m1_fraction=0.,fan_request=True,heat_enable=False)
        if (not self.qualified or self.motor_limit_C is None or self.gear_limit_C is None
                or self.current_limit_A is None or self.minimum_running_rpm is None):
            return dict(state='QUALIFICATION_HOLD',m1_fraction=0.,fan_request=True,heat_enable=False)
        if not run_request:
            self.run_latched = False
        elif start_edge:
            self.run_latched = True
        if not self.run_latched or buffer_full:
            return dict(state='BUFFER_HOLD' if self.run_latched and buffer_full else 'IDLE',m1_fraction=0.,fan_request=True,heat_enable=False)
        t = max(temperatures[k] for k in ('s1_wall','s2_shear','s2_screen'))
        lim=MATERIALS[material]
        f=min(1.,max(0.,(lim['stop_C']-t)/(lim['stop_C']-lim['derate_C'])))
        return dict(state='RUN' if f==1 else 'DERATE',m1_fraction=f,fan_request=True,heat_enable=True,
                    coupled_axes='S1_AND_S2_COMMON_SPEED_ONLY')


def allocate_power(m1_bus_W: float, m2_bus_W: float, auxiliaries_W: float,
                   heater_request_W: float, budget_W: float = 500.0):
    """Reference admission only; PSU 792 W rating does not raise this budget."""
    vals = [m1_bus_W, m2_bus_W, auxiliaries_W, heater_request_W, budget_W]
    if not all(math.isfinite(v) and v >= 0 for v in vals) or budget_W > 500.0:
        raise ValueError('Invalid DC bus power or operating budget; phase current cannot substitute for bus power')
    reserved = m1_bus_W + m2_bus_W + auxiliaries_W
    if reserved > budget_W:
        return dict(admitted=False, heater_W=0., total_W=0.,
                    reason='OPERATING_BUDGET_REJECT')
    heater_W = min(heater_request_W, budget_W - reserved)
    return dict(admitted=True, heater_W=heater_W, total_W=reserved + heater_W,
                reason=('HEATER_DERATED_AT_OPERATING_CAP'
                        if heater_W < heater_request_W
                        else 'REFERENCE_ALLOCATION_ONLY'))
