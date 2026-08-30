within PLA_PET_Recycler.Scenarios;
model GaugeLossRundown
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION,gaugeFailureTime=1500,gaugeFailureDuration=5,formingInitialState=GeneratedControl.FORMING_REQUALIFYING,useQualificationFixture=true,operatorRethreadConfirmationTime=600);
  parameter String acceptance="feeder and winding off within latency, ten-second screw decay and bounded thermal hold";
end GaugeLossRundown;
