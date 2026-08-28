within PLA_PET_Recycler.Components;
model Puller
  input Real speedCommand;
  input Boolean enable;
  output Real speed(start=0,fixed=true);
equation
  der(speed)=((if enable then speedCommand else 0)-speed)/0.12;
end Puller;
