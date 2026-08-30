within PLA_PET_Recycler.Scenarios;
model ProcessPreheatToExtrusionTransition
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.PREHEATING,nextState=GeneratedControl.EXTRUSION,transitionTime=2);
  parameter String acceptance="screw is enabled only after leaving shred mode; phase peak remains <=500 W";
end ProcessPreheatToExtrusionTransition;
