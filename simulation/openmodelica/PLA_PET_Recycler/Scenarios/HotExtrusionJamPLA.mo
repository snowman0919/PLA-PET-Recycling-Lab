within PLA_PET_Recycler.Scenarios;
model HotExtrusionJamPLA
  extends Systems.ThermalExtruderSystem(material=1,targetRPM=16,blockageStart=1500,blockageRamp=120);
  parameter String acceptance="steady hot extrusion develops pressure/current trip and bounded safe thermal hold";
end HotExtrusionJamPLA;
