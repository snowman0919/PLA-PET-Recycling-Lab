within PLA_PET_Recycler.Scenarios;
model GaugeDropout
  extends Systems.DynamicSpoolSystem(initialFill=0.5,gaugeValid=false);
  parameter String protectedRequirement="SYS-GAUGE-FAIL-01";
  parameter String estimatedParameters="static communication loss";
  parameter String acceptance="spool motor torque is zero on invalid gauge";
end GaugeDropout;
