within PLA_PET_Recycler.Scenarios;
model PreheatCoolingStartupProbe
  extends Systems.ProcessArbitrationSystem(
    initialState=GeneratedControl.IDLE,
    nextState=GeneratedControl.PREHEATING,
    transitionTime=2,
    coolingFeedbackCalibrationValid=true,
    coolingFeedbackValid=true);
  parameter String acceptance="fan-only startup probe proves healthy feedback for 1.5 s before PREHEATING commits";
end PreheatCoolingStartupProbe;
