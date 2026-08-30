within PLA_PET_Recycler.Scenarios;
model DancerLimit
  extends Systems.DynamicSpoolSystem(initialFill=0.5,traverseDisturbance=12);
  parameter String protectedRequirement="SYS-SPOOL-FAULT-01";
  parameter String estimatedParameters="12 N traverse disturbance";
  parameter String acceptance="dancer-limit or tension fault becomes true";
end DancerLimit;
