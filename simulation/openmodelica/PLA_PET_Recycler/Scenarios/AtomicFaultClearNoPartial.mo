within PLA_PET_Recycler.Scenarios;
model AtomicFaultClearNoPartial
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.FAULT,nextState=GeneratedControl.IDLE,transitionTime=2,restartPermission=false);
  parameter String acceptance="a refused fault clear preserves FAULT atomically and leaves every hazardous output off";
end AtomicFaultClearNoPartial;
