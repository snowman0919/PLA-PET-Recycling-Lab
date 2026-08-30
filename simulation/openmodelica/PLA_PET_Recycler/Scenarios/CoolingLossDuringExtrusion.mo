within PLA_PET_Recycler.Scenarios;
model CoolingLossDuringExtrusion
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION,coolingLossTime=1500,formingInitialState=GeneratedControl.FORMING_REQUALIFYING,useQualificationFixture=true,operatorRethreadConfirmationTime=600);
  parameter String protectedRequirement="SYS-COOL-COUPLE-01";
  parameter String acceptance="cooling permission loss sets fan contribution to zero and raises downstream temperature";
end CoolingLossDuringExtrusion;
