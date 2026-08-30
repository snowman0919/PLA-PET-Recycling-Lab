within PLA_PET_Recycler.Scenarios;
model PurgeScrewFault
  extends Systems.FullCoupledSystem(material=1,pendingMaterial=2,processState=GeneratedControl.MAINTENANCE_PURGE,purgeStartTime=1400,wastePathConfirmed=true,purgeVisualConfirmed=true,screenCleanConfirmed=true,hopperCleanConfirmed=true,temperatureTransitionConfirmed=true,finalMaterialConfirmed=true,forceJam=true);
  parameter String acceptance="screw drive trip prevents purge completion and pending-material activation";
end PurgeScrewFault;
