within PLA_PET_Recycler.Scenarios;
model PurgeWastePathBlocked
  extends Systems.FullCoupledSystem(material=1,pendingMaterial=2,processState=GeneratedControl.MAINTENANCE_PURGE,wastePathConfirmed=false,purgeVisualConfirmed=true,screenCleanConfirmed=true,hopperCleanConfirmed=true,temperatureTransitionConfirmed=true,finalMaterialConfirmed=true);
  parameter String acceptance="without manual waste-path confirmation no purge actuator starts and pending PET cannot activate";
end PurgeWastePathBlocked;
