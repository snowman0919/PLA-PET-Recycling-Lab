within PLA_PET_Recycler.Scenarios;
model DancerHardStopSensitivity
  extends Systems.DynamicSpoolSystem(initialFill=0.5,traverseDisturbance=24);
  parameter String classification="SENSITIVITY_ONLY_NOT_NORMAL_SAFE_BEHAVIOR";
  parameter String acceptance="mechanical contact reaction is exported separately and cannot satisfy nominal jam acceptance";
end DancerHardStopSensitivity;
