within PLA_PET_Recycler.Scenarios;
model SpoolJamPropagation
  extends Systems.DynamicSpoolSystem(initialFill=1.0,spoolJammed=true,lineSpeedCommand=0.025);
  parameter String acceptance="puller initially feeds then line fault stops feed and prevents unbounded accumulation";
end SpoolJamPropagation;
