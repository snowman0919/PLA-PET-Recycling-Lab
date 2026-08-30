within PLA_PET_Recycler.Scenarios;
model ReliefOpeningPET
  extends Systems.ThermalExtruderSystem(material=2,targetRPM=18,bulkDensity=350,blockageStart=1500,blockageRamp=120);
  parameter String acceptance="PET retainer opens, bypass grows, normal extrusion latches off and residual pressure is bounded";
end ReliefOpeningPET;
