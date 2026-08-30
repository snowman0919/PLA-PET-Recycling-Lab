within PLA_PET_Recycler.Scenarios;
model CoolingLossRundown
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION,coolingLossTime=1500,coolingLossDuration=5,formingInitialState=GeneratedControl.FORMING_REQUALIFYING,useQualificationFixture=true,operatorRethreadConfirmationTime=600,operatorRethreadSecondConfirmationTime=1650);
  parameter String acceptance="current feedback, not command PWM, detects cooling loss and starts common rundown after 1.5 s dwell";
end CoolingLossRundown;
