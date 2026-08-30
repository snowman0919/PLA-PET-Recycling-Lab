within PLA_PET_Recycler.Scenarios;
model PurgeFeedApprovalMissing
  extends Systems.FullCoupledSystem(material=1,pendingMaterial=2,processState=GeneratedControl.MAINTENANCE_PURGE,wastePathConfirmed=true,purgeFeedApproved=false,purgeVisualConfirmed=true,screenCleanConfirmed=true,hopperCleanConfirmed=true,temperatureTransitionConfirmed=true,finalMaterialConfirmed=true);
  parameter String acceptance="waste path confirmation alone cannot start screw, feed, or puller without the independent single-use purge feed approval";
end PurgeFeedApprovalMissing;
