within PLA_PET_Recycler.Systems;
model MaterialSessionSystem
  parameter Integer processState=GeneratedControl.IDLE;
  parameter Integer initialMaterial=1 "1 PLA, 2 PET";
  parameter Integer requestedMaterial=2;
  parameter Real requestTime=1;
  parameter Real purgeAckTime=2;
  parameter Real screenAckTime=3;
  parameter Real hopperAckTime=4;
  parameter Real temperatureAckTime=5;
  parameter Real finalConfirmTime=6;
  discrete Integer activeMaterial(start=initialMaterial,fixed=true);
  discrete Integer pendingMaterial(start=0,fixed=true);
  discrete Integer materialSession(start=if initialMaterial==1 then GeneratedControl.MATERIAL_PLA_ACTIVE else GeneratedControl.MATERIAL_PET_ACTIVE,fixed=true);
  Boolean feedStopped;
  Boolean productionAllowed;
equation
  feedStopped=processState==GeneratedControl.IDLE;
  productionAllowed=materialSession==GeneratedControl.MATERIAL_PLA_ACTIVE or materialSession==GeneratedControl.MATERIAL_PET_ACTIVE;
  when time>=requestTime and requestedMaterial<>pre(activeMaterial) and feedStopped then
    pendingMaterial=requestedMaterial;
    materialSession=GeneratedControl.MATERIAL_PURGE_REQUIRED;
  elsewhen time>=purgeAckTime and pre(materialSession)==GeneratedControl.MATERIAL_PURGE_REQUIRED then
    pendingMaterial=pre(pendingMaterial);
    materialSession=GeneratedControl.MATERIAL_SCREEN_CLEAN_REQUIRED;
  elsewhen time>=screenAckTime and pre(materialSession)==GeneratedControl.MATERIAL_SCREEN_CLEAN_REQUIRED then
    pendingMaterial=pre(pendingMaterial);
    materialSession=GeneratedControl.MATERIAL_HOPPER_CLEAN_REQUIRED;
  elsewhen time>=hopperAckTime and pre(materialSession)==GeneratedControl.MATERIAL_HOPPER_CLEAN_REQUIRED then
    pendingMaterial=pre(pendingMaterial);
    materialSession=GeneratedControl.MATERIAL_TEMPERATURE_TRANSITION_REQUIRED;
  elsewhen time>=temperatureAckTime and pre(materialSession)==GeneratedControl.MATERIAL_TEMPERATURE_TRANSITION_REQUIRED then
    pendingMaterial=pre(pendingMaterial);
    materialSession=GeneratedControl.MATERIAL_FINAL_CONFIRM_REQUIRED;
  elsewhen time>=finalConfirmTime and pre(materialSession)==GeneratedControl.MATERIAL_FINAL_CONFIRM_REQUIRED then
    activeMaterial=pre(pendingMaterial);
    pendingMaterial=0;
    materialSession=if pre(pendingMaterial)==1 then GeneratedControl.MATERIAL_PLA_ACTIVE else GeneratedControl.MATERIAL_PET_ACTIVE;
  end when;
end MaterialSessionSystem;
