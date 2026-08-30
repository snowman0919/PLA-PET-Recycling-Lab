within PLA_PET_Recycler.Scenarios;
model FullJam
  extends Systems.CoupledShredderSystem(rightMaterial=4,leftMaterial=4,jamLoadTorque=13.5);
  parameter String protectedRequirement="SYS-JAM-01";
  parameter String estimatedParameters="both rotors locked by configured 13.5 N.m/shaft jam load";
  parameter String acceptance="production threshold and startup grace lead to three bounded retries and latched fault";
end FullJam;
