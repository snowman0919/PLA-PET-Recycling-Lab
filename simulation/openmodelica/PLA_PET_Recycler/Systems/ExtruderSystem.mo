within PLA_PET_Recycler.Systems;
model ExtruderSystem
  parameter Real targetRPM=Parameters.screwRPMPLA;
  parameter Integer material=1 "1 PLA, 2 PET";
  parameter Real jamStart=1e9;
  parameter Real stopTime=1e9;
  Components.ExtrusionLoadSurrogate load(jamStart=jamStart);
  Components.ScrewDrive drive;
  Real screwRPM;
  Real throughputGPH;
  Real residenceTime;
  Real purgeTime;
  Real mechanicalPower;
  Boolean torqueTrip;
equation
  drive.targetSpeed=targetRPM*2*Modelica.Constants.pi/60;
  drive.loadTorque=load.torque;
  drive.enable=time<stopTime and load.torque<22;
  screwRPM=drive.speed*60/(2*Modelica.Constants.pi);
  throughputGPH=max(0,screwRPM)*(if material==1 then Parameters.throughputPerRPMPLA else Parameters.throughputPerRPMPET);
  residenceTime=16/max(0.1,screwRPM*0.68*0.87)*60;
  purgeTime=100/max(1,throughputGPH)*3600;
  mechanicalPower=abs(drive.motorTorque*drive.speed);
  torqueTrip=load.torque>=22;
end ExtruderSystem;
