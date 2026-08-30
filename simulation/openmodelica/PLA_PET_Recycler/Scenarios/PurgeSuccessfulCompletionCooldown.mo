within PLA_PET_Recycler.Scenarios;
model PurgeSuccessfulCompletionCooldown
  Systems.ProcessArbitrationSystem process(
    initialState=GeneratedControl.MAINTENANCE_PURGE,
    nextState=GeneratedControl.COOLDOWN,
    transitionTime=481,
    cooldownInitialTemperatureC=4000,
    cooldownRateCPerS=8);
  Systems.MaterialSessionSystem session(
    requestTime=0.2,
    purgePreheatReadyTime=0.4,
    wastePathConfirmTime=0.6,
    screenAckTime=482,
    hopperAckTime=482.2,
    temperatureAckTime=482.4,
    finalConfirmTime=482.6,
    purgeVisualConfirmed=true);
  Integer processState;
  Integer materialSession;
  Boolean coolingEnabled;
  Boolean screwEnabled;
  Boolean processHeaterEnabled;
  Boolean feederEnabled;
  Boolean pullerEnabled;
  Boolean spoolerEnabled;
  Boolean traverseEnabled;
  Real cooldownProcessTemperature;
  Boolean purgeCompletionSatisfied;
  Boolean pendingMaterialActivated;
equation
  session.processState=process.processState;
  processState=process.processState;
  materialSession=session.materialSession;
  coolingEnabled=process.coolingEnabled;
  screwEnabled=process.screwEnabled;
  processHeaterEnabled=process.processHeaterEnabled;
  feederEnabled=process.feederEnabled;
  pullerEnabled=process.pullerEnabled;
  spoolerEnabled=process.spoolerEnabled;
  traverseEnabled=process.traverseEnabled;
  cooldownProcessTemperature=process.cooldownProcessTemperature;
  purgeCompletionSatisfied=session.purgeCompletionSatisfied;
  pendingMaterialActivated=session.pendingMaterial==0 and session.activeMaterial==2;
end PurgeSuccessfulCompletionCooldown;
