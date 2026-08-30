within PLA_PET_Recycler.Scenarios;
model MotorLoadStep
  extends Systems.CoupledShredderSystem(material=1,targetRPM=32,engagement=0.6,engagementAfter=1.35,engagementStepTime=4);
  parameter String acceptance="speed recovers from a tooth-load step without false jam, fuse trip or overspeed";
end MotorLoadStep;
