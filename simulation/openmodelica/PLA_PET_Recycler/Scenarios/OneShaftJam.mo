within PLA_PET_Recycler.Scenarios;
model OneShaftJam
  extends Systems.CoupledShredderSystem(rightMaterial=4,leftMaterial=0,overloadDwell=0.01,currentThreshold=4.0);
  parameter String protectedRequirement="SYS-JAM-01, phase load path";
  parameter String estimatedParameters="35 N.m locked-hook surrogate";
  parameter String acceptance="current plus RPM dwell detects jam and phase/fuse response is bounded";
end OneShaftJam;
