within PLA_PET_Recycler.Scenarios;
model FeederLossDuringExtrusion
  extends Systems.FullCoupledSystem(material=1,processState=GeneratedControl.EXTRUSION,feederLossTime=1500,formingInitialState=GeneratedControl.FORMING_REQUALIFYING,useQualificationFixture=true,operatorRethreadConfirmationTime=600);
  parameter String protectedRequirement="SYS-FEED-COUPLE-01";
  parameter String acceptance="feed loss drains bounded inventory and net mass flow decays";
end FeederLossDuringExtrusion;
