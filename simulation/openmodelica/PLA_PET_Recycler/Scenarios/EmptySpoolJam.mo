within PLA_PET_Recycler.Scenarios;
model EmptySpoolJam
  extends Systems.DynamicSpoolSystem(initialFill=0,spoolJammed=true);
  parameter String acceptance="normal locked-rotor detection commands controlled pause before mechanical hard stop";
end EmptySpoolJam;
