within PLA_PET_Recycler.Scenarios;
model PurgePLAtoPET
  extends Systems.FullCoupledSystem(material=1,pendingMaterial=2,processState=GeneratedControl.MAINTENANCE_PURGE,purgeStartTime=1400,wastePathConfirmed=true,purgeVisualConfirmed=true,screenCleanConfirmed=true,hopperCleanConfirmed=true,temperatureTransitionConfirmed=true,finalMaterialConfirmed=true);
  parameter String acceptance="previous PLA thermal profile, bounded screw, waste-only output, elapsed/revolutions/temperature/visual/ordered confirmations before PET activation";
end PurgePLAtoPET;
