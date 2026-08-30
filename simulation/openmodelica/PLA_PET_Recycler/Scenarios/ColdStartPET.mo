within PLA_PET_Recycler.Scenarios;
model ColdStartPET
  extends Systems.CoupledShredderSystem(material=2,targetRPM=24);
  parameter String acceptance="PET acceleration reaches regulated speed without false jam";
end ColdStartPET;
