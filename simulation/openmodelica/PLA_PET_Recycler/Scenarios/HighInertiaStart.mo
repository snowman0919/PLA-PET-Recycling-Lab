within PLA_PET_Recycler.Scenarios;
model HighInertiaStart
  extends Systems.CoupledShredderSystem(material=1,targetRPM=32,rightRotor(J=0.001023),leftRotor(J=0.001023));
  parameter String acceptance="four-times rotor inertia starts without a false jam";
end HighInertiaStart;
