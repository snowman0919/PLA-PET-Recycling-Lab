within PLA_PET_Recycler.Systems;
model MaterialSessionSystem
  input Integer processState;
  parameter Integer initialMaterial=1 "1 PLA, 2 PET";
  parameter Integer requestedMaterial=2;
  parameter Real requestTime=1;
  parameter Real purgePreheatReadyTime=2;
  parameter Real wastePathConfirmTime=3;
  parameter Real screenAckTime=150;
  parameter Real hopperAckTime=151;
  parameter Real temperatureAckTime=152;
  parameter Real finalConfirmTime=153;
  parameter Real abortTime=1e9;
  parameter Real purgeScrewRPM=16*GeneratedControl.purgeScrewScale;
  parameter Boolean purgeTemperatureStable=true;
  parameter Boolean purgeNoFault=true;
  parameter Boolean purgeVisualConfirmed=true;
  discrete Integer activeMaterial(start=initialMaterial,fixed=true);
  discrete Integer pendingMaterial(start=0,fixed=true);
  discrete Integer materialSession(start=if initialMaterial==1 then GeneratedControl.MATERIAL_PLA_ACTIVE else GeneratedControl.MATERIAL_PET_ACTIVE,fixed=true);
  discrete Real purgeRunStart(start=-1,fixed=true);
  discrete Boolean abortRecoveryLatched(start=false,fixed=true);
  Real purgeElapsed;
  Real purgeScrewRevolutions(start=0,fixed=true);
  Boolean processStopped;
  Boolean wastePathConfirmed;
  Boolean productionAllowed;
  Boolean purgeCompletionSatisfied;
  Boolean purgeAborted;
algorithm
  when initial() then
    activeMaterial := initialMaterial;
    pendingMaterial := 0;
    materialSession := if initialMaterial==1 then GeneratedControl.MATERIAL_PLA_ACTIVE else GeneratedControl.MATERIAL_PET_ACTIVE;
    purgeRunStart := -1;
    abortRecoveryLatched := false;
  elsewhen sample(0,0.2) then
    if time>=abortTime and pre(materialSession)==GeneratedControl.MATERIAL_PURGE_RUNNING then
      materialSession := GeneratedControl.MATERIAL_PURGE_PREHEAT_REQUIRED;
      purgeRunStart := -1;
      abortRecoveryLatched := true;
    elseif time>=requestTime and requestedMaterial<>pre(activeMaterial) and processStopped and (pre(materialSession)==GeneratedControl.MATERIAL_PLA_ACTIVE or pre(materialSession)==GeneratedControl.MATERIAL_PET_ACTIVE) then
      pendingMaterial := requestedMaterial;
      materialSession := GeneratedControl.MATERIAL_PURGE_PREHEAT_REQUIRED;
    elseif time>=purgePreheatReadyTime and not pre(abortRecoveryLatched) and pre(materialSession)==GeneratedControl.MATERIAL_PURGE_PREHEAT_REQUIRED and purgeTemperatureStable then
      materialSession := GeneratedControl.MATERIAL_PURGE_READY_CONFIRM_REQUIRED;
    elseif wastePathConfirmed and pre(materialSession)==GeneratedControl.MATERIAL_PURGE_READY_CONFIRM_REQUIRED and processState==GeneratedControl.MAINTENANCE_PURGE then
      materialSession := GeneratedControl.MATERIAL_PURGE_RUNNING;
      purgeRunStart := time;
    elseif purgeCompletionSatisfied and pre(materialSession)==GeneratedControl.MATERIAL_PURGE_RUNNING then
      materialSession := GeneratedControl.MATERIAL_SCREEN_CLEAN_REQUIRED;
    elseif time>=screenAckTime and processState==GeneratedControl.IDLE and pre(materialSession)==GeneratedControl.MATERIAL_SCREEN_CLEAN_REQUIRED then
      materialSession := GeneratedControl.MATERIAL_HOPPER_CLEAN_REQUIRED;
    elseif time>=hopperAckTime and processState==GeneratedControl.IDLE and pre(materialSession)==GeneratedControl.MATERIAL_HOPPER_CLEAN_REQUIRED then
      materialSession := GeneratedControl.MATERIAL_TEMPERATURE_TRANSITION_REQUIRED;
    elseif time>=temperatureAckTime and processState==GeneratedControl.IDLE and pre(materialSession)==GeneratedControl.MATERIAL_TEMPERATURE_TRANSITION_REQUIRED then
      materialSession := GeneratedControl.MATERIAL_FINAL_CONFIRM_REQUIRED;
    elseif time>=finalConfirmTime and processState==GeneratedControl.IDLE and pre(materialSession)==GeneratedControl.MATERIAL_FINAL_CONFIRM_REQUIRED then
      activeMaterial := pre(pendingMaterial);
      pendingMaterial := 0;
      materialSession := if pre(pendingMaterial)==1 then GeneratedControl.MATERIAL_PLA_ACTIVE else GeneratedControl.MATERIAL_PET_ACTIVE;
    end if;
  end when;
equation
  processStopped=processState==GeneratedControl.IDLE or processState==GeneratedControl.PREHEATING or processState==GeneratedControl.MAINTENANCE_PURGE;
  wastePathConfirmed=time>=wastePathConfirmTime;
  productionAllowed=materialSession==GeneratedControl.MATERIAL_PLA_ACTIVE or materialSession==GeneratedControl.MATERIAL_PET_ACTIVE;
  purgeElapsed=if purgeRunStart>=0 then time-purgeRunStart else 0;
  der(purgeScrewRevolutions)=if materialSession==GeneratedControl.MATERIAL_PURGE_RUNNING and processState==GeneratedControl.MAINTENANCE_PURGE and purgeNoFault then purgeScrewRPM/60 else 0;
  purgeCompletionSatisfied=purgeElapsed>=GeneratedControl.purgeMinTime and purgeScrewRevolutions>=GeneratedControl.purgeMinScrewRevolutions and purgeTemperatureStable and purgeNoFault and purgeVisualConfirmed;
  purgeAborted=time>=abortTime and not productionAllowed and materialSession==GeneratedControl.MATERIAL_PURGE_PREHEAT_REQUIRED;
end MaterialSessionSystem;
