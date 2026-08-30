within PLA_PET_Recycler.Scenarios;
model PurgeCoolingStartupProbe
  extends Systems.ProcessArbitrationSystem(
    initialState=GeneratedControl.IDLE,
    nextState=GeneratedControl.MAINTENANCE_PURGE,
    transitionTime=2,
    coolingFeedbackCalibrationValid=true,
    coolingFeedbackValid=true,
    wastePathConfirmed=false);
  parameter String acceptance="purge thermal preheat starts with a fan-only proof while screw/feed remain blocked until waste approval";
end PurgeCoolingStartupProbe;
