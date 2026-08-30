within PLA_PET_Recycler.Scenarios;
model MotorRatedLoadStrict
  extends Systems.CoupledShredderSystem(material=1,engagement=1.08,targetRPM=28);
  parameter String protectedRequirement="SYS-DRV-RATED-STRICT-01";
  parameter String acceptance="rated current <=8.2 A, steady speed error <=10 percent, overshoot <=25 percent";
end MotorRatedLoadStrict;
