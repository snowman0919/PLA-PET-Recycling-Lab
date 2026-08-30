within PLA_PET_Recycler.Scenarios;
model QualityViolationRequalification
  Systems.FormingChainSupervisor supervisor(
    requestedFaultReason=GeneratedControl.FAULT_NONE,
    gaugeValid=true,
    gaugeU95=0.01,
    diameterError=if time>=1 and time<2 then 0.08 else 0,
    ovality=0.01,
    pullerSaturated=false,
    coolingFeedbackValid=true,
    qualityValid=not (time>=1 and time<2),
    stableFlow=true,
    qualityInterlockArmed=true,
    emergencyStop=false,
    operatorRethreadConfirmed=time>=35,
    explicitFaultClear=false);
  Integer state;
  Boolean spoolEligible;
  Boolean wasteMode;
  parameter String acceptance="diameter violation immediately inhibits winding and enters REQUALIFYING without rundown; full thresholds plus explicit rethread are required for NORMAL";
equation
  state=supervisor.state;
  spoolEligible=supervisor.spoolEligible;
  wasteMode=supervisor.wasteMode;
end QualityViolationRequalification;
