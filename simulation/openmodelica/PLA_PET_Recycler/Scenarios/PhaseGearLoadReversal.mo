within PLA_PET_Recycler.Scenarios;
model PhaseGearLoadReversal
  extends Systems.CoupledShredderSystem(rightMaterial=4,leftMaterial=0,jamLoadTorque=20,jamReleaseTime=7);
  parameter String protectedRequirement="SYS-PHASE-REV-01";
  parameter String acceptance="reverse recovery keeps phase error and phase torque below allowables";
end PhaseGearLoadReversal;
