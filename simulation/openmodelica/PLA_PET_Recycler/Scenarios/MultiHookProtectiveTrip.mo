within PLA_PET_Recycler.Scenarios;
model MultiHookProtectiveTrip
  extends Systems.CoupledShredderSystem(material=2,engagement=2.4);
  parameter String protectedRequirement="SYS-MULTIHOOK-PROTECT-01";
  parameter String acceptance="electrical retry or sacrificial fuse acts before 34 N.m phase and 48 N.m shaft allowables";
end MultiHookProtectiveTrip;
