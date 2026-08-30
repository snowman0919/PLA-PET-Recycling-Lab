within PLA_PET_Recycler.Scenarios;
model FullSystemPLA
  extends Systems.FullCoupledSystem(material=1);
  parameter String protectedRequirement="SYS-COUPLED-01, SYS-POWER-01";
  parameter String estimatedParameters="coupled digital PLA baseline";
  parameter String acceptance="bus power <=600 W and no propagated fault in nominal state";
end FullSystemPLA;
