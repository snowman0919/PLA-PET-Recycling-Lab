within PLA_PET_Recycler.Systems;
model ShredderSystem
  parameter Integer loadMode=1;
  parameter Real jamStart=1e9;
  parameter Real stopTime=1e9;
  parameter Real forcedLoad=0;
  parameter Real forcedRequest=0;
  parameter Boolean retryLogic=false;
  parameter Real phaseComplianceRadPerNm=0.00035;
  parameter Real phaseBacklashRad=0.006;
  Components.CalibratedDCDrive drive;
  Components.InputTorqueFuse inputFuse;
  Components.CutterLoadSurrogate load(mode=loadMode,jamStart=jamStart,forcedLoad=forcedLoad);
  Components.CutterRotor rightRotor;
  Components.CutterRotor leftRotor;
  Components.SafetyController controller(jamStart=if retryLogic then jamStart else 1e9);
  Real speedCommand;
  Real requestedTorque;
  Real transmittedTorque;
  Real cutterTorque;
  Real phaseError;
  Real phaseTorque;
  Real phaseSeparatingForce;
  Real chainForce;
  Real bearingLoad;
  Real frameReaction;
  Boolean electricalTrip;
  Boolean fuseOperating;
  Boolean faultLatched;
  Integer retryCount;
equation
  controller.permission=time<stopTime;
  retryCount=controller.retryCount;
  faultLatched=controller.latchedFault;
  speedCommand=32*2*Modelica.Constants.pi/60;
  requestedTorque=if time>=stopTime or faultLatched then 0 else
    (if retryLogic then controller.commandSign else 1)*(forcedRequest+min(Parameters.normalTorque,load.torque)+0.8*(speedCommand-abs(rightRotor.speed)));
  inputFuse.requestedTorque=requestedTorque;
  transmittedTorque=inputFuse.transmittedTorque;
  fuseOperating=inputFuse.operating;
  drive.torqueRequest=transmittedTorque;
  drive.enable=time<stopTime and not faultLatched;
  cutterTorque=drive.torque;
  rightRotor.driveTorque=cutterTorque;
  rightRotor.loadTorque=load.torque/2*tanh(20*rightRotor.speed);
  leftRotor.driveTorque=-cutterTorque;
  leftRotor.loadTorque=load.torque/2*tanh(20*leftRotor.speed);
  phaseError=rightRotor.angle+leftRotor.angle
    +phaseComplianceRadPerNm*cutterTorque
    +(if abs(cutterTorque)>0.01 then sign(cutterTorque)*phaseBacklashRad/2 else 0);
  phaseTorque=2200*phaseError;
  phaseSeparatingForce=abs(phaseTorque)/Generated.CADParameters.phaseGearRadius*tan(Modelica.Constants.pi/9);
  chainForce=abs(cutterTorque)/Generated.CADParameters.cutterSprocketRadius;
  bearingLoad=load.torque/(2*0.029)+chainForce+phaseSeparatingForce;
  frameReaction=bearingLoad+abs(cutterTorque)/0.12;
  electricalTrip=abs(load.torque)>=Parameters.electricalTripTorque;
end ShredderSystem;
