within PLA_PET_Recycler.Scenarios;
model PurgeHeaterFault
  extends Systems.FullCoupledSystem(material=1,pendingMaterial=2,processState=GeneratedControl.MAINTENANCE_PURGE,purgeStartTime=1400,wastePathConfirmed=true,purgeVisualConfirmed=true,screenCleanConfirmed=true,hopperCleanConfirmed=true,temperatureTransitionConfirmed=true,finalMaterialConfirmed=true,heaterSensorFault=true);
  parameter String acceptance="invalid thermal chain inhibits purge motion and material activation";
end PurgeHeaterFault;
