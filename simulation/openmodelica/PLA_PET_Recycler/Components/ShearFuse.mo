within PLA_PET_Recycler.Components;
model ShearFuse
  parameter Real tripTorque=10.35 "N.m at gearmotor output for 22 N.m cutter equivalent";
  parameter Real intactStiffness=800 "N.m/rad, calibrated torsional surrogate";
  parameter Real separatedStiffness=0.02 "N.m/rad, fragment-retainer residual";
  parameter Real damping=1.0 "N.m.s/rad";
  Modelica.Mechanics.Rotational.Interfaces.Flange_a driveSide;
  Modelica.Mechanics.Rotational.Interfaces.Flange_b loadSide;
  discrete Boolean broken(start=false,fixed=true);
  Real transmittedTorque;
  Real relativeAngle;
equation
  relativeAngle=driveSide.phi-loadSide.phi;
  transmittedTorque=if broken then separatedStiffness*relativeAngle else intactStiffness*relativeAngle+damping*der(relativeAngle);
  driveSide.tau=-transmittedTorque;
  loadSide.tau=transmittedTorque;
  when abs(transmittedTorque)>=tripTorque then
    broken=true;
  end when;
end ShearFuse;
