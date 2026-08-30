within PLA_PET_Recycler.Scenarios;
model MotorNoLoadStart
  extends Systems.CoupledShredderSystem(material=0,targetRPM=32);
  parameter String protectedRequirement="SYS-DRV-01";
  parameter String estimatedParameters="R,L,Kt,Ke,J and gearbox efficiency from digital reference";
  parameter String acceptance="starts without jam or fuse trip; no-load current is finite";
end MotorNoLoadStart;
