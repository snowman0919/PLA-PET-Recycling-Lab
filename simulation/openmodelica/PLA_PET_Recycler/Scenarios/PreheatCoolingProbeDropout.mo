within PLA_PET_Recycler.Scenarios;
model PreheatCoolingProbeDropout
  extends Systems.ProcessArbitrationSystem(
    initialState=GeneratedControl.IDLE,
    nextState=GeneratedControl.PREHEATING,
    transitionTime=2,
    coolingFeedbackCalibrationValid=true,
    coolingFeedbackValid=true,
    coolingFeedbackDropoutStart=2.5,
    coolingFeedbackDropoutDuration=0.5);
  parameter String acceptance="startup feedback dropout resets the proof timer; only a new consecutive 1.5 s window commits PREHEATING";
end PreheatCoolingProbeDropout;
