within PLA_PET_Recycler.Scenarios;
model PreheatRequiresExplicitExtrusionArm
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.PREHEATING,nextState=GeneratedControl.REQUALIFYING,transitionTime=2,extrusionArmed=false);
  parameter String acceptance="failed start without explicit arm rolls the phase back to PREHEATING and cannot energize motion";
end PreheatRequiresExplicitExtrusionArm;
