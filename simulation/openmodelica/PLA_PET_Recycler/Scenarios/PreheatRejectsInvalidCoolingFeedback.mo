within PLA_PET_Recycler.Scenarios;
model PreheatRejectsInvalidCoolingFeedback
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.IDLE,nextState=GeneratedControl.PREHEATING,transitionTime=2,coolingFeedbackValid=false);
  parameter String acceptance="PREHEATING start rolls back to IDLE when live cooling feedback is invalid";
end PreheatRejectsInvalidCoolingFeedback;
