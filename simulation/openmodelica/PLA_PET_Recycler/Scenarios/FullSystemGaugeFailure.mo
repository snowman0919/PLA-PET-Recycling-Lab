within PLA_PET_Recycler.Scenarios;
model FullSystemGaugeFailure
  extends Systems.FullCoupledSystem(material=1,gaugeValid=false);
  parameter String protectedRequirement="SYS-GAUGE-FAIL-01, SYS-COUPLED-01";
  parameter String estimatedParameters="static gauge communication loss";
  parameter String acceptance="feeder, extrusion and spool commands enter safe stopped state";
end FullSystemGaugeFailure;
