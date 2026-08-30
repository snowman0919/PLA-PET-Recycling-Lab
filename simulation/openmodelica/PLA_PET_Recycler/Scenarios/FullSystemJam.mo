within PLA_PET_Recycler.Scenarios;
model FullSystemJam
  extends Systems.FullCoupledSystem(material=2,forceJam=true);
  parameter String protectedRequirement="SYS-JAM-01, SYS-COUPLED-01";
  parameter String estimatedParameters="persistent shredder and screw/spool jam propagation";
  parameter String acceptance="feed/puller disable and all rotating subsystems reach bounded fault state";
end FullSystemJam;
