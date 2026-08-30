within PLA_PET_Recycler.Scenarios;
model FullSpoolJam
  extends Systems.DynamicSpoolSystem(initialFill=1,spoolJammed=true);
  parameter String acceptance="full-spool jam stops at controlled threshold before hard-stop contact";
end FullSpoolJam;
