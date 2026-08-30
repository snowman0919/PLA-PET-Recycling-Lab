within PLA_PET_Recycler.Systems;
model PullerTachMonitorSystem
  parameter Real commandStartTime=0;
  parameter Real firstPulseTime=0;
  parameter Real runningLossTime=1e9;
  Boolean pullerCommanded;
  Boolean startupGraceActive;
  Boolean tachQualified;
  Boolean tachHealthy;
  Boolean tachFailure;
  Boolean rundownRequested;
equation
  pullerCommanded=time>=commandStartTime;
  startupGraceActive=pullerCommanded and time-commandStartTime<GeneratedControl.pullerTachStartupGrace;
  tachQualified=pullerCommanded and time>=firstPulseTime and firstPulseTime<=commandStartTime+GeneratedControl.pullerTachStartupGrace;
  tachHealthy=tachQualified and time<runningLossTime;
  tachFailure=pullerCommanded and not startupGraceActive and not tachHealthy;
  rundownRequested=tachFailure;
end PullerTachMonitorSystem;
