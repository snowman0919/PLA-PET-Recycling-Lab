within PLA_PET_Recycler.Scenarios;
model FaultCoolingRetention
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.FAULT,coolingFeedbackValid=true);
  parameter String acceptance="a non-cooling FAULT keeps validated cooling on while every hazardous actuator remains off";
end FaultCoolingRetention;
