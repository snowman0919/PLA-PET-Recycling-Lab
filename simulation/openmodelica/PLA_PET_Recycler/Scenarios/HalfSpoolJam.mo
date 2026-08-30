within PLA_PET_Recycler.Scenarios;
model HalfSpoolJam
  extends Systems.DynamicSpoolSystem(initialFill=0.5,spoolJammed=true);
  parameter String acceptance="half-spool jam stops at controlled threshold before hard-stop contact";
end HalfSpoolJam;
