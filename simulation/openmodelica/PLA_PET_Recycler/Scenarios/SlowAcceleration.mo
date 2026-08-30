within PLA_PET_Recycler.Scenarios;
model SlowAcceleration
  extends Systems.CoupledShredderSystem(material=1,targetRPM=32,motor(rotorInertia=0.0021));
  parameter String acceptance="slow acceleration remains inside startup grace and does not reverse";
end SlowAcceleration;
