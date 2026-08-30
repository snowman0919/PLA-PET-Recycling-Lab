within PLA_PET_Recycler.Scenarios;
model RetryFailure
  extends Systems.CoupledShredderSystem(rightMaterial=4,leftMaterial=4,jamLoadTorque=9.5);
  parameter String protectedRequirement="SYS-JAM-01";
  parameter String estimatedParameters="persistent two-shaft jam";
  parameter String acceptance="persistent overload becomes latched fault and motor enable is removed";
end RetryFailure;
