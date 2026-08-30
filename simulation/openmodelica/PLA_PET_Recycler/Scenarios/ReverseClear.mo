within PLA_PET_Recycler.Scenarios;
model ReverseClear
  extends Systems.CoupledShredderSystem(rightMaterial=4,leftMaterial=4,jamLoadTorque=13.5,jamReleaseTime=4.10);
  parameter String protectedRequirement="SYS-JAM-01";
  parameter String estimatedParameters="one-sided jam load remains applied during reverse";
  parameter String acceptance="negative bounded duty follows qualified jam detection";
end ReverseClear;
