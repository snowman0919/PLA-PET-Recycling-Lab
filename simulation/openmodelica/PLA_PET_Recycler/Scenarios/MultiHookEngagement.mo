within PLA_PET_Recycler.Scenarios;
model MultiHookEngagement
  extends Systems.CoupledShredderSystem(material=2,engagement=1.80);
  parameter String protectedRequirement="SYS-CUT-KIN-01, SYS-TORQUE-01";
  parameter String estimatedParameters="simultaneous multi-hook load multiplier";
  parameter String acceptance="protective trip occurs before phase or shaft hierarchy limit";
end MultiHookEngagement;
