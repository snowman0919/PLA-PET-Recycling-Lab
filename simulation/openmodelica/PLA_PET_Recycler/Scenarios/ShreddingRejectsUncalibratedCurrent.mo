within PLA_PET_Recycler.Scenarios;
model ShreddingRejectsUncalibratedCurrent
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.IDLE,nextState=GeneratedControl.SHREDDING,transitionTime=2,currentSensorCalibrationValid=false);
  parameter String acceptance="SHREDDING start rolls back to IDLE when current-sensor calibration is not ready";
end ShreddingRejectsUncalibratedCurrent;
