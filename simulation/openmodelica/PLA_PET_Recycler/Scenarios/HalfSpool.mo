within PLA_PET_Recycler.Scenarios;
model HalfSpool
  extends Systems.DynamicSpoolSystem(initialFill=0.5);
  parameter String protectedRequirement="SYS-SPOOL-01";
  parameter String estimatedParameters="linear radius/inertia interpolation";
  parameter String acceptance="dancer within +/-25 deg and tension below 8 N";
end HalfSpool;
