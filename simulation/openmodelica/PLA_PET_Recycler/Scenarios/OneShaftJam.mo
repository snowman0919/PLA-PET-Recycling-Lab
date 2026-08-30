within PLA_PET_Recycler.Scenarios;
model OneShaftJam
  extends Systems.CoupledShredderSystem(rightMaterial=4,leftMaterial=0);
  parameter String protectedRequirement="SYS-JAM-01, phase load path";
  parameter String estimatedParameters="one rotor locked by configured 20 N.m shaft jam load";
  parameter String acceptance="current plus RPM dwell detects jam and phase/fuse response is bounded";
end OneShaftJam;
