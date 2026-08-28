within PLA_PET_Recycler.Components;
model ScrewDrive
  parameter Real J = Generated.CADParameters.screwJ;
  input Real targetSpeed;
  input Real loadTorque;
  input Boolean enable;
  output Real speed(start=0,fixed=true);
  output Real motorTorque;
equation
  motorTorque = if enable then max(-22,min(22,1.5*(targetSpeed-speed)+loadTorque)) else 0;
  J*der(speed)=motorTorque-loadTorque-0.02*speed;
end ScrewDrive;
