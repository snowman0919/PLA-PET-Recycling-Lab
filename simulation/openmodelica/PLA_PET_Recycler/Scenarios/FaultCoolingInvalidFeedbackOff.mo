within PLA_PET_Recycler.Scenarios;
model FaultCoolingInvalidFeedbackOff
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.FAULT,coolingFeedbackValid=false);
  parameter String acceptance="FAULT cooling is removed when cooling feedback is invalid; hazardous actuators remain off";
end FaultCoolingInvalidFeedbackOff;
