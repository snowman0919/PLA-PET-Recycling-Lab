within PLA_PET_Recycler.Scenarios;
model SpoolPermissionLossRundown
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION,spoolerPermissionLossTime=1500,formingInitialState=GeneratedControl.FORMING_REQUALIFYING,useQualificationFixture=true,operatorRethreadConfirmationTime=600);
  parameter String acceptance="spool permission loss disables winding immediately and routes residual forming flow to bounded waste rundown";
end SpoolPermissionLossRundown;
