within PLA_PET_Recycler.Scenarios;
model ReverseClear
  extends Systems.CoupledShredderSystem(rightMaterial=4,leftMaterial=2,overloadDwell=0.01,currentThreshold=4.0,jamReleaseTime=0.35);
  parameter String protectedRequirement="SYS-JAM-01";
  parameter String estimatedParameters="one-sided jam surrogate remains applied during reverse";
  parameter String acceptance="negative bounded duty follows qualified jam detection";
end ReverseClear;
