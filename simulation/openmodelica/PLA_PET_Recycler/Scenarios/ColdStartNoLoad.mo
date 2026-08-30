within PLA_PET_Recycler.Scenarios;
model ColdStartNoLoad
  extends Systems.CoupledShredderSystem(material=0,targetRPM=32);
  parameter String acceptance="RPM deficit during startup grace does not trigger reverse or fault";
end ColdStartNoLoad;
