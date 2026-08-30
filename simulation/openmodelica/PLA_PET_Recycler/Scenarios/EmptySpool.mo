within PLA_PET_Recycler.Scenarios;
model EmptySpool
  extends Systems.DynamicSpoolSystem(initialFill=0);
  parameter String protectedRequirement="SYS-SPOOL-01";
  parameter String estimatedParameters="empty-spool inertia and radius";
  parameter String acceptance="dancer within +/-25 deg and tension below 8 N";
end EmptySpool;
