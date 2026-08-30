within PLA_PET_Recycler.Scenarios;
model BrownoutLikeVoltageDrop
  extends Systems.CoupledShredderSystem(material=1,targetRPM=32,motor(supplyVoltage=18));
  parameter String acceptance="RPM deficit alone at 18 V cannot satisfy canonical jam conjunction";
end BrownoutLikeVoltageDrop;
