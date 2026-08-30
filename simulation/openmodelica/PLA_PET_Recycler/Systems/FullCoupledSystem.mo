within PLA_PET_Recycler.Systems;
model FullCoupledSystem
  parameter Integer material=1;
  parameter Boolean gaugeValid=true;
  parameter Boolean forceJam=false;
  parameter Boolean emergencyStop=false;
  CoupledShredderSystem shredder(material=if forceJam then 4 else material,enabled=not emergencyStop);
  ThermalExtruderSystem extruder(material=material,enabled=not emergencyStop and gaugeValid,screwJammed=forceJam);
  DynamicSpoolSystem spool(gaugeValid=gaugeValid and not emergencyStop,spoolJammed=forceJam);
  Real busPower;
  Boolean feederEnable;
  Boolean pullerEnable;
  Boolean safeState;
equation
  feederEnable=extruder.ready and gaugeValid and not emergencyStop and not forceJam;
  pullerEnable=gaugeValid and not emergencyStop and not forceJam;
  busPower=24*abs(shredder.motor.current)+extruder.power1+extruder.power2+extruder.power3+extruder.powerDie+24*spool.motorCurrent+45;
  safeState=if emergencyStop then not shredder.motor.enable and not feederEnable and not pullerEnable and extruder.power1+extruder.power2+extruder.power3+extruder.powerDie<=360 else true;
end FullCoupledSystem;

