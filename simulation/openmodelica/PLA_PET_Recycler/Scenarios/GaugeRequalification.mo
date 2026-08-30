within PLA_PET_Recycler.Scenarios;
model GaugeRequalification
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION,gaugeFailureTime=1500,gaugeFailureDuration=5,formingInitialState=GeneratedControl.FORMING_REQUALIFYING,useQualificationFixture=true,operatorRethreadConfirmationTime=600,operatorRethreadSecondConfirmationTime=1900);
  parameter String acceptance="gauge loss drives rundown/hold/requalification; winding remains off until 20 samples, U95/diameter/ovality, nominal transport delay and explicit rethread";
end GaugeRequalification;
