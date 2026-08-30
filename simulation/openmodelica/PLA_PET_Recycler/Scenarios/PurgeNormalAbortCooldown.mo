within PLA_PET_Recycler.Scenarios;
model PurgeNormalAbortCooldown
  Systems.ProcessArbitrationSystem process(
    initialState=GeneratedControl.MAINTENANCE_PURGE,
    nextState=GeneratedControl.COOLDOWN,
    transitionTime=2,
    cooldownInitialTemperatureC=90,
    cooldownRateCPerS=8);
  Systems.MaterialSessionSystem session(
    requestTime=0.2,
    purgePreheatReadyTime=0.4,
    wastePathConfirmTime=0.6,
    abortTime=2,
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
end PurgeNormalAbortCooldown;
