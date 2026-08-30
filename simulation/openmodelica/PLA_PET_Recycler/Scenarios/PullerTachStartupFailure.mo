within PLA_PET_Recycler.Scenarios;
model PullerTachStartupFailure
  extends Systems.PullerTachMonitorSystem(firstPulseTime=1e9,runningLossTime=1e9);
  parameter String acceptance="missing startup tach is tolerated only for 1.5 s, then starts the normal bounded rundown without a renewed grace";
end PullerTachStartupFailure;
