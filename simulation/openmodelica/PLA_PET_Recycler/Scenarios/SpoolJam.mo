within PLA_PET_Recycler.Scenarios;
model SpoolJam
  extends Systems.DynamicSpoolSystem(initialFill=0.5,spoolJammed=true);
  parameter String protectedRequirement="SYS-SPOOL-FAULT-01";
  parameter String estimatedParameters="locked spool rotor";
  parameter String acceptance="brake locks rotation, line imbalance detects jam and upstream line feed reaches bounded safe pause";
end SpoolJam;
