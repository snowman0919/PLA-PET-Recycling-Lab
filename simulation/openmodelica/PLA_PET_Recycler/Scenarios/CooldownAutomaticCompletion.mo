within PLA_PET_Recycler.Scenarios;
model CooldownAutomaticCompletion
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.COOLDOWN,nextState=GeneratedControl.IDLE,temperatureChannelsValid=true,coolingFeedbackValid=true,cooldownInitialTemperatureC=90,cooldownRateCPerS=8);
  parameter String acceptance="COOLDOWN retains healthy cooling and automatically enters IDLE only after all process channels are valid and <=60 C";
end CooldownAutomaticCompletion;
