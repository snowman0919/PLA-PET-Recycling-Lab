within PLA_PET_Recycler.Scenarios;
model FullJam
  extends Systems.CoupledShredderSystem(rightMaterial=4,leftMaterial=4,jamLoadTorque=9.5);
  parameter String protectedRequirement="SYS-JAM-01";
  parameter String estimatedParameters="both rotors loaded by 9.5 N.m/shaft (19 N.m total), above electrical trip and below 22 N.m fuse";
  parameter String acceptance="production threshold and startup grace lead to three bounded retries and latched fault";
end FullJam;
