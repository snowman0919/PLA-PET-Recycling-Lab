within PLA_PET_Recycler.Scenarios;
model EmergencyStop
  extends Systems.CoupledShredderSystem(material=2,stopTime=2);
  parameter String protectedRequirement="SYS-SAFE-01";
  parameter String estimatedParameters="coast inertia and friction";
  parameter String acceptance="PWM command and motor enable become zero at 2 s";
end EmergencyStop;
