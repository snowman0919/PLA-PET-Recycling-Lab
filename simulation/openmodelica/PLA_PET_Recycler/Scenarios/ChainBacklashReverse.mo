within PLA_PET_Recycler.Scenarios;
model ChainBacklashReverse
  extends Systems.CoupledShredderSystem(material=4,overloadDwell=0.01);
  parameter String scenarioClass="SENSITIVITY_ONLY";
  parameter String protectedRequirement="SYS-DRV-BACKLASH-01";
  parameter String estimatedParameters="0.35 deg chain backlash and elastic stiffness";
  parameter String acceptance="reverse transient has bounded torque and does not bypass DRV-F01";
end ChainBacklashReverse;
