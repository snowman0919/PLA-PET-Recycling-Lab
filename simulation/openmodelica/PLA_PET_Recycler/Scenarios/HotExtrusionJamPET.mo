within PLA_PET_Recycler.Scenarios;
model HotExtrusionJamPET
  extends Systems.ThermalExtruderSystem(material=2,targetRPM=18,blockageStart=1500,blockageRamp=120);
  parameter String acceptance="steady PET extrusion develops pressure/current trip and bounded safe thermal hold";
end HotExtrusionJamPET;
