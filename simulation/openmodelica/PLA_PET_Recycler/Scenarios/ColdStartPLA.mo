within PLA_PET_Recycler.Scenarios;
model ColdStartPLA
  extends Systems.CoupledShredderSystem(material=1,targetRPM=32);
  parameter String acceptance="PLA acceleration reaches regulated speed without false jam";
end ColdStartPLA;
