within PLA_PET_Recycler.Scenarios;
model ProcessPreheatToExtrusionTransition
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.PREHEATING,nextState=GeneratedControl.REQUALIFYING,transitionTime=2);
  parameter String acceptance="explicit arm enters REQUALIFYING before EXTRUSION; phase peak remains <=500 W";
end ProcessPreheatToExtrusionTransition;
