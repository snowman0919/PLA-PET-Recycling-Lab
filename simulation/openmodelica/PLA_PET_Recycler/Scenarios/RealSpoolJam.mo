within PLA_PET_Recycler.Scenarios;
model RealSpoolJam
  extends Systems.DynamicSpoolSystem(initialFill=0.5,spoolJammed=true);
  parameter String acceptance="locked rotor creates detectable length imbalance and bounded safe pause";
end RealSpoolJam;
