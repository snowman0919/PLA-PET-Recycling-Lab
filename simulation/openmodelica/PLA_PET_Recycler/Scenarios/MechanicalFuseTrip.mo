within PLA_PET_Recycler.Scenarios;
model MechanicalFuseTrip
  extends Systems.CoupledShredderSystem(material=4,currentThreshold=40,overloadDwell=4);
  parameter String protectedRequirement="SYS-TORQUE-01";
  parameter String estimatedParameters="DRV-F01 10.35 N.m motor-side trip threshold";
  parameter String acceptance="one-shot fuse opens before 34/48 N.m downstream hierarchy";
end MechanicalFuseTrip;
