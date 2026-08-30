within PLA_PET_Recycler.Scenarios;
model LeftShaftJam
  extends Systems.CoupledShredderSystem(rightMaterial=0,leftMaterial=4,jamLoadTorque=20);
  parameter String protectedRequirement="SYS-JAM-LEFT-01";
  parameter String acceptance="three-retry trip with bounded phase and shaft torque on left-shaft load transfer";
end LeftShaftJam;
