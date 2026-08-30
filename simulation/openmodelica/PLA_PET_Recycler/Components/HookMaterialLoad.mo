within PLA_PET_Recycler.Components;
model HookMaterialLoad
  parameter Integer material=1 "0 no load, 1 PLA, 2 PET body, 3 PET folded, 4 full jam";
  parameter Real releaseTime=1e9 "s; jam coupon clears to PET body after this time";
  parameter Real engagement=1.0 "dimensionless sensitivity factor";
  parameter Real phaseOffset=0 "rad";
  Modelica.Mechanics.Rotational.Interfaces.Flange_a shaft;
  Real toothAngle;
  Real capture;
  Real buckle;
  Real fracture;
  Real releaseZone;
  Real loadTorque;
  Real speed;
  Integer activeMaterial;
equation
  speed=der(shaft.phi);
  activeMaterial=if material==4 and time>=releaseTime then 2 else material;
  toothAngle=mod(shaft.phi+phaseOffset,2*Modelica.Constants.pi/7)/(2*Modelica.Constants.pi/7);
  capture=max(0,min(1,toothAngle/0.22));
  buckle=max(0,1-abs(toothAngle-0.40)/0.18);
  fracture=max(0,1-abs(toothAngle-(if activeMaterial==1 then 0.58 else 0.66))/(if activeMaterial==1 then 0.07 else 0.14));
  releaseZone=max(0,1-abs(toothAngle-0.86)/0.10);
  loadTorque=engagement*(if activeMaterial==0 then 0.35 else if activeMaterial==1 then 2.0+2.2*capture+7.8*fracture-1.0*releaseZone else if activeMaterial==2 then 1.5+2.0*capture+4.8*buckle+5.2*fracture else if activeMaterial==3 then 2.5+3.0*capture+7.0*buckle+8.5*fracture else if speed<0 then 5.0 else 35.0);
  shaft.tau=loadTorque*tanh(40*speed);
end HookMaterialLoad;
