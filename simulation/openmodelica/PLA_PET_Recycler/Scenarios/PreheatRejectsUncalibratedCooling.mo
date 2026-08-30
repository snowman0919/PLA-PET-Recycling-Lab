within PLA_PET_Recycler.Scenarios;
model PreheatRejectsUncalibratedCooling
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.IDLE,nextState=GeneratedControl.PREHEATING,transitionTime=2,coolingFeedbackCalibrationValid=false);
  parameter String acceptance="PREHEATING start rolls back to IDLE when cooling-feedback calibration is not ready";
end PreheatRejectsUncalibratedCooling;
