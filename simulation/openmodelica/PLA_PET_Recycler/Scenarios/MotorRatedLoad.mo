within PLA_PET_Recycler.Scenarios;
model MotorRatedLoad
  extends Systems.CoupledShredderSystem(material=1,engagement=1.10,targetRPM=28);
  parameter String protectedRequirement="SYS-DRV-01, SYS-TORQUE-01";
  parameter String estimatedParameters="rated motor constants and 1.35 hook engagement";
  parameter String acceptance="rated current <=8.2 A screening and no mechanical fuse trip";
end MotorRatedLoad;
