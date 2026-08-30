within PLA_PET_Recycler.Scenarios;
model FullSystemGaugeFailure
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION,gaugeFailureTime=1500,formingInitialState=GeneratedControl.FORMING_REQUALIFYING,useQualificationFixture=true,operatorRethreadConfirmationTime=600);
  parameter String protectedRequirement="SYS-GAUGE-FAIL-01, SYS-COUPLED-01";
  parameter String estimatedParameters="static gauge communication loss";
  parameter String acceptance="feeder, extrusion and spool commands enter safe stopped state";
end FullSystemGaugeFailure;
