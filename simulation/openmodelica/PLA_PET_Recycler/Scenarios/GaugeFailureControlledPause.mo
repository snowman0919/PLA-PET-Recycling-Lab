within PLA_PET_Recycler.Scenarios;
model GaugeFailureControlledPause
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION,gaugeFailureTime=1500);
  parameter String protectedRequirement="SYS-GAUGE-PAUSE-01";
  parameter String acceptance="feed immediate stop, ten-second screw rundown, spool/puller pause and sixty-second thermal safe hold";
end GaugeFailureControlledPause;
