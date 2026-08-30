within PLA_PET_Recycler.Systems;
model FormingChainSupervisor
  parameter Integer material=1 "1 PLA, 2 PET";
  parameter Integer initialState=GeneratedControl.FORMING_NORMAL;
  parameter Real samplePeriod=GeneratedControl.gaugeSamplePeriod;
  parameter Real sampleOffset=samplePeriod/2;
  input Integer requestedFaultReason=GeneratedControl.FAULT_NONE;
  input Boolean gaugeValid=true;
  input Real gaugeU95=0.01 "mm";
  input Real diameterError=0 "mm";
  input Real ovality=0 "mm";
  input Boolean pullerSaturated=false;
  input Boolean coolingFeedbackValid=true;
  input Boolean qualityValid=true;
  input Boolean stableFlow=true;
  input Boolean qualityInterlockArmed=true;
  input Boolean emergencyStop=false;
  input Boolean operatorRethreadConfirmed=false;
  input Boolean explicitFaultClear=false;
  discrete Integer state(start=initialState,fixed=true);
  discrete Integer faultReason(start=GeneratedControl.FAULT_NONE,fixed=true);
  discrete Real stateEntryTime(start=0,fixed=true);
  discrete Real recoveryStartTime(start=-1,fixed=true);
  discrete Real qualityStableStart(start=-1,fixed=true);
  discrete Integer consecutiveValidSamples(start=0,fixed=true);
  discrete Real coolingRecoveryStart(start=-1,fixed=true);
  Boolean faultActive;
  Boolean feederPermitted;
  Boolean screwPermitted;
  Boolean pullerPermitted;
  Boolean spoolerPermitted;
  Boolean traversePermitted;
  Boolean coolingPermitted;
  Boolean coolingRecoveryProbe;
  Boolean heaterPermitted;
  Boolean spoolEligible;
  Boolean wasteMode;
  Boolean freshQualityPreflight;
  Real screwRundownScale;
algorithm
  when initial() then
    state := initialState;
    faultReason := GeneratedControl.FAULT_NONE;
    stateEntryTime := time;
    recoveryStartTime := -1;
    qualityStableStart := -1;
    consecutiveValidSamples := 0;
    coolingRecoveryStart := -1;
  elsewhen sample(sampleOffset,samplePeriod) then
    if emergencyStop then
      state := GeneratedControl.FORMING_LATCHED_FAULT;
      faultReason := if requestedFaultReason == GeneratedControl.FAULT_NONE then GeneratedControl.FAULT_DANCER_HARD_LIMIT else requestedFaultReason;
      stateEntryTime := time;
      recoveryStartTime := -1;
      qualityStableStart := -1;
      consecutiveValidSamples := 0;
    elseif pre(state) == GeneratedControl.FORMING_NORMAL and faultActive then
      state := if requestedFaultReason == GeneratedControl.FAULT_DANCER_HARD_LIMIT then GeneratedControl.FORMING_LATCHED_FAULT else GeneratedControl.FORMING_RUNDOWN;
      faultReason := requestedFaultReason;
      stateEntryTime := time;
      recoveryStartTime := -1;
      qualityStableStart := -1;
      consecutiveValidSamples := 0;
    elseif pre(state) == GeneratedControl.FORMING_NORMAL and qualityInterlockArmed and not freshQualityPreflight then
      state := GeneratedControl.FORMING_REQUALIFYING;
      faultReason := GeneratedControl.FAULT_NONE;
      stateEntryTime := time;
      recoveryStartTime := -1;
      qualityStableStart := -1;
      consecutiveValidSamples := 0;
    elseif pre(state) == GeneratedControl.FORMING_RUNDOWN and time - pre(stateEntryTime) >= GeneratedControl.rundownDuration then
      state := GeneratedControl.FORMING_THERMAL_HOLD;
      stateEntryTime := time;
    elseif pre(state) == GeneratedControl.FORMING_THERMAL_HOLD and time - pre(stateEntryTime) >= GeneratedControl.thermalHoldDuration then
      if pre(faultReason) == GeneratedControl.FAULT_COOLING_FAILURE then
        if coolingFeedbackValid then
          if pre(coolingRecoveryStart) < 0 then
            coolingRecoveryStart := time;
          elseif time-pre(coolingRecoveryStart) >= GeneratedControl.coolingFeedbackDwell then
            state := GeneratedControl.FORMING_REQUALIFYING;
            stateEntryTime := time;
            recoveryStartTime := -1;
            qualityStableStart := -1;
            consecutiveValidSamples := 0;
            coolingRecoveryStart := -1;
          end if;
        else
          coolingRecoveryStart := -1;
        end if;
      else
        state := if faultActive then GeneratedControl.FORMING_LATCHED_FAULT else GeneratedControl.FORMING_REQUALIFYING;
        stateEntryTime := time;
        recoveryStartTime := -1;
        qualityStableStart := -1;
        consecutiveValidSamples := 0;
      end if;
    elseif pre(state) == GeneratedControl.FORMING_REQUALIFYING and faultActive and not (pre(faultReason) == GeneratedControl.FAULT_COOLING_FAILURE and coolingFeedbackValid) then
      state := GeneratedControl.FORMING_RUNDOWN;
      faultReason := requestedFaultReason;
      stateEntryTime := time;
      recoveryStartTime := -1;
      qualityStableStart := -1;
      consecutiveValidSamples := 0;
    elseif pre(state) == GeneratedControl.FORMING_REQUALIFYING and pre(consecutiveValidSamples) >= GeneratedControl.requalGaugeSamples and pre(qualityStableStart) >= 0 and time - pre(qualityStableStart) >= GeneratedControl.requalStableDuration and pre(recoveryStartTime) >= 0 and time - pre(recoveryStartTime) >= GeneratedControl.transportDelayByMaterial[material] then
      state := GeneratedControl.FORMING_READY_TO_RETHREAD;
      stateEntryTime := time;
    elseif pre(state) == GeneratedControl.FORMING_READY_TO_RETHREAD and not freshQualityPreflight then
      state := GeneratedControl.FORMING_REQUALIFYING;
      stateEntryTime := time;
      recoveryStartTime := -1;
      qualityStableStart := -1;
      consecutiveValidSamples := 0;
    elseif pre(state) == GeneratedControl.FORMING_READY_TO_RETHREAD and operatorRethreadConfirmed and (not faultActive or (pre(faultReason) == GeneratedControl.FAULT_COOLING_FAILURE and coolingFeedbackValid)) and freshQualityPreflight then
      state := GeneratedControl.FORMING_NORMAL;
      faultReason := GeneratedControl.FAULT_NONE;
      stateEntryTime := time;
    elseif pre(state) == GeneratedControl.FORMING_LATCHED_FAULT and explicitFaultClear and not faultActive then
      state := GeneratedControl.FORMING_REQUALIFYING;
      faultReason := GeneratedControl.FAULT_NONE;
      stateEntryTime := time;
      recoveryStartTime := -1;
      qualityStableStart := -1;
      consecutiveValidSamples := 0;
    end if;

    if pre(state) == GeneratedControl.FORMING_REQUALIFYING then
      if stableFlow and gaugeValid and gaugeU95 <= GeneratedControl.requalU95Max and abs(diameterError) <= GeneratedControl.requalDiameterTolerance and ovality <= GeneratedControl.requalOvalityMax and not pullerSaturated and coolingFeedbackValid then
        consecutiveValidSamples := pre(consecutiveValidSamples) + 1;
        if pre(recoveryStartTime) < 0 then
          recoveryStartTime := time;
        end if;
        if pre(qualityStableStart) < 0 then
          qualityStableStart := time;
        end if;
      else
        consecutiveValidSamples := 0;
        recoveryStartTime := -1;
        qualityStableStart := -1;
      end if;
    elseif pre(state) <> GeneratedControl.FORMING_READY_TO_RETHREAD then
      consecutiveValidSamples := 0;
      qualityStableStart := -1;
    end if;
  end when;
equation
  faultActive=requestedFaultReason <> GeneratedControl.FAULT_NONE;
  freshQualityPreflight=qualityValid and gaugeValid and gaugeU95<=GeneratedControl.requalU95Max and abs(diameterError)<=GeneratedControl.requalDiameterTolerance and ovality<=GeneratedControl.requalOvalityMax and not pullerSaturated and coolingFeedbackValid;
  screwRundownScale=if state == GeneratedControl.FORMING_NORMAL or state == GeneratedControl.FORMING_REQUALIFYING or state == GeneratedControl.FORMING_READY_TO_RETHREAD then 1 else if state == GeneratedControl.FORMING_RUNDOWN then max(0,1-(time-stateEntryTime)/GeneratedControl.rundownDuration) else 0;
  feederPermitted=state == GeneratedControl.FORMING_NORMAL or state == GeneratedControl.FORMING_REQUALIFYING;
  screwPermitted=screwRundownScale > 0;
  pullerPermitted=(state == GeneratedControl.FORMING_NORMAL or state == GeneratedControl.FORMING_REQUALIFYING or (state == GeneratedControl.FORMING_RUNDOWN and time-stateEntryTime<GeneratedControl.pullerWasteDuration)) and faultReason <> GeneratedControl.FAULT_PULLER_DRIVER_FAILURE and faultReason <> GeneratedControl.FAULT_PULLER_TACH_FAILURE and faultReason <> GeneratedControl.FAULT_DANCER_HARD_LIMIT;
  spoolEligible=state == GeneratedControl.FORMING_NORMAL and not faultActive and (not qualityInterlockArmed or freshQualityPreflight);
  spoolerPermitted=spoolEligible;
  traversePermitted=spoolEligible;
  coolingRecoveryProbe=not emergencyStop and state == GeneratedControl.FORMING_THERMAL_HOLD and faultReason == GeneratedControl.FAULT_COOLING_FAILURE and time-stateEntryTime>=GeneratedControl.thermalHoldDuration;
  coolingPermitted=not emergencyStop and (faultReason <> GeneratedControl.FAULT_COOLING_FAILURE or coolingRecoveryProbe or state == GeneratedControl.FORMING_REQUALIFYING or state == GeneratedControl.FORMING_READY_TO_RETHREAD);
  heaterPermitted=not emergencyStop and (state == GeneratedControl.FORMING_NORMAL or state == GeneratedControl.FORMING_RUNDOWN or state == GeneratedControl.FORMING_THERMAL_HOLD or state == GeneratedControl.FORMING_REQUALIFYING or state == GeneratedControl.FORMING_READY_TO_RETHREAD);
  wasteMode=not spoolEligible;
end FormingChainSupervisor;
