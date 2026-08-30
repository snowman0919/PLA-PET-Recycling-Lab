within PLA_PET_Recycler.Scenarios;
model SingleHookImpact
  extends Systems.CoupledShredderSystem(material=3,engagement=0.55);
  parameter String protectedRequirement="SYS-CUT-KIN-01";
  parameter String estimatedParameters="single folded-PET tooth impulse";
  parameter String acceptance="peak phase force and shaft torque remain below digital screening limits";
end SingleHookImpact;
