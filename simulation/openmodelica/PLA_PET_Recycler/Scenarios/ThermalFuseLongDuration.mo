within PLA_PET_Recycler.Scenarios;
model ThermalFuseLongDuration
  extends Systems.ThermalExtruderSystem(material=2,stuckOnZone=3,screwEnabled=false);
  parameter String acceptance="long-duration stuck-on reaches safe equilibrium or independent 300 C fuse operation";
end ThermalFuseLongDuration;
