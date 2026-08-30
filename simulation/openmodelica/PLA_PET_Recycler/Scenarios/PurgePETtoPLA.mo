within PLA_PET_Recycler.Scenarios;
model PurgePETtoPLA
  extends Systems.FullCoupledSystem(material=2,pendingMaterial=1,processState=GeneratedControl.MAINTENANCE_PURGE,purgeStartTime=1500,wastePathConfirmed=true,purgeVisualConfirmed=true,screenCleanConfirmed=true,hopperCleanConfirmed=true,temperatureTransitionConfirmed=true,finalMaterialConfirmed=true);
  parameter String acceptance="previous PET thermal profile remains active until complete ordered purge commits PLA";
end PurgePETtoPLA;
