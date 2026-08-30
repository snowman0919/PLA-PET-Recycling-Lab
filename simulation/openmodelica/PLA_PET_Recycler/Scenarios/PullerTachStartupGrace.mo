within PLA_PET_Recycler.Scenarios;
model PullerTachStartupGrace
  extends Systems.PullerTachMonitorSystem(firstPulseTime=1.1,runningLossTime=1e9);
  parameter String acceptance="20 pulse/rev tach becomes valid inside the single 1.5 s command-start grace without a false forming fault";
end PullerTachStartupGrace;
