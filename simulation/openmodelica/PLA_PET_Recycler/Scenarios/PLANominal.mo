within PLA_PET_Recycler.Scenarios;
model PLANominal
  extends Systems.CoupledShredderSystem(material=1,targetRPM=32,engagement=0.85);
  parameter String protectedRequirement="SYS-SHARED-01, SYS-TORQUE-01";
  parameter String estimatedParameters="GMP60 electrical constants, cutter engagement";
  parameter String acceptance="no latched jam; cutter torque below 14 N.m continuous target";
end PLANominal;
