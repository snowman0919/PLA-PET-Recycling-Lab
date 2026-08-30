within PLA_PET_Recycler.Scenarios;
model FullJam
  extends Systems.CoupledShredderSystem(rightMaterial=4,leftMaterial=4,overloadDwell=0.01,currentThreshold=4.0);
  parameter String protectedRequirement="SYS-JAM-01";
  parameter String estimatedParameters="both rotors locked by 35 N.m/hook surrogate";
  parameter String acceptance="jam detection requires current plus RPM dwell and enters bounded response";
end FullJam;
