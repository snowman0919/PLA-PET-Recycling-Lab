within PLA_PET_Recycler.Scenarios;
model PETNominal
  extends Systems.CoupledShredderSystem(material=2,targetRPM=28);
  parameter String protectedRequirement="SYS-SHARED-01, SYS-TORQUE-01";
  parameter String estimatedParameters="PET body hook-load surrogate; Gate-1 pending";
  parameter String acceptance="no latched jam; current and RPM stay inside profile thresholds";
end PETNominal;
