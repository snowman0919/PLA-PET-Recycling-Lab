within PLA_PET_Recycler.Scenarios;
model PurgeCoolingFault
  extends Systems.FullCoupledSystem(material=1,pendingMaterial=2,processState=GeneratedControl.MAINTENANCE_PURGE,purgeStartTime=1350,wastePathConfirmed=true,purgeVisualConfirmed=true,screenCleanConfirmed=true,hopperCleanConfirmed=true,temperatureTransitionConfirmed=true,finalMaterialConfirmed=true,coolingLossTime=1500);
  parameter String acceptance="purge cooling-feedback loss latches the phase fault after 1.5 s dwell, zeros hazardous outputs in one cycle, and cannot commit pending material";
end PurgeCoolingFault;
