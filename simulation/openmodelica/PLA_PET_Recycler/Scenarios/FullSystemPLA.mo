within PLA_PET_Recycler.Scenarios;
model FullSystemPLA
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION);
  parameter String protectedRequirement="SYS-COUPLED-01, SYS-POWER-01";
  parameter String estimatedParameters="coupled digital PLA baseline";
  parameter String acceptance="normal phase <=500 W, >=100 W reserve and all independent invariants true";
end FullSystemPLA;
