within PLA_PET_Recycler.Scenarios;
model SpoolerPermissionLoss
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION,spoolerPermissionLossTime=1500,formingInitialState=GeneratedControl.FORMING_REQUALIFYING,useQualificationFixture=true,operatorRethreadConfirmationTime=600);
  parameter String protectedRequirement="SYS-SPOOL-PERMISSION-01";
  parameter String acceptance="permission reaches actuator, removes torque and initiates upstream safe pause";
end SpoolerPermissionLoss;
