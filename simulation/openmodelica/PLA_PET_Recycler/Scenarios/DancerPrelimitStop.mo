within PLA_PET_Recycler.Scenarios;
model DancerPrelimitStop
  extends Systems.DynamicSpoolSystem(initialFill=0.5,traverseDisturbance=8);
  parameter String acceptance="warning precedes controlled stop and no hard-stop contact occurs";
end DancerPrelimitStop;
