within PLA_PET_Recycler.Scenarios;
model ReliefOpeningPLA
  extends Systems.ThermalExtruderSystem(material=1,targetRPM=16,blockageStart=1500,blockageRamp=120);
  parameter String acceptance="retainer opens, bypass grows, normal extrusion latches off and residual pressure is bounded";
end ReliefOpeningPLA;
