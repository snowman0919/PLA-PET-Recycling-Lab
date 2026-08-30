within PLA_PET_Recycler.Scenarios;
model FullSpool
  extends Systems.DynamicSpoolSystem(initialFill=1);
  parameter String protectedRequirement="SYS-SPOOL-01";
  parameter String estimatedParameters="full-spool inertia and radius";
  parameter String acceptance="motor current and dancer remain bounded at maximum radius";
end FullSpool;
