within PLA_PET_Recycler.Scenarios;
model SpoolJam
  extends Systems.DynamicSpoolSystem(initialFill=0.5,spoolJammed=true);
  parameter String protectedRequirement="SYS-SPOOL-FAULT-01";
  parameter String estimatedParameters="locked spool rotor";
  parameter String acceptance="spool torque command is zero and no hidden puller-force claim is made";
end SpoolJam;
