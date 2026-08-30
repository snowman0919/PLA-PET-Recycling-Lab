within PLA_PET_Recycler.Scenarios;
model PurgeEmergencyStop
  extends Systems.FullCoupledSystem(material=1,pendingMaterial=2,processState=GeneratedControl.MAINTENANCE_PURGE,purgeStartTime=1400,wastePathConfirmed=true,purgeVisualConfirmed=true,screenCleanConfirmed=true,hopperCleanConfirmed=true,temperatureTransitionConfirmed=true,finalMaterialConfirmed=true,emergencyStopTime=1550);
  parameter String acceptance="E-stop removes purge screw/feed/heater/cooling and never commits pending material";
end PurgeEmergencyStop;
