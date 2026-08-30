within PLA_PET_Recycler.Scenarios;
model ProcessShredToPreheatTransition
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.SHREDDING,nextState=GeneratedControl.PREHEATING,transitionTime=2);
  parameter String acceptance="shredder is removed before process heat is permitted";
end ProcessShredToPreheatTransition;
