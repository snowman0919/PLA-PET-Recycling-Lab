within PLA_PET_Recycler;
package Generated
package CADParameters
  constant String revision = "solid-manifold-openmodelica-v0.4";
  constant String baselineSHA256 = "84c4ed0fd1a2b8d972c8725be54c1479e24eb94f01e441128434deefb5af64ea";
  constant Real cutterDiscMass = 0.0684185363429 "kg";
  constant Real cutterRotorMass = 1.12825424517 "kg";
  constant Real cutterRotorJ = 0.000253394623572 "kg.m2";
  constant Real screwMass = 0.30789075164 "kg";
  constant Real screwJ = 6.51334629861e-06 "kg.m2";
  constant Real cutterSprocketRadius = 0.0364869297035 "m";
  constant Real motorSprocketRadius = 0.0184008869908 "m";
  constant Real phaseGearRadius = 0.024 "m";
  constant Real shaftCenters[2,3] = [0.105,0,0.590;0.153,0,0.590] "m";
  constant Real bearingCenters[4,3] = [0.105,0.315,0.590;0.105,0.455,0.590;0.153,0.315,0.590;0.153,0.455,0.590] "m";
  constant Real spoolEmptyJ = 0.0018683 "kg.m2";
  constant Real spoolFullJ = 0.0072063 "kg.m2";
  constant Real assemblyMass = 71.5506633366 "kg";
  constant Real assemblyCOM[3] = {0.265230056911,0.298425551148,0.424749150312};
  constant Real assemblyInertia[3,3] = [6.60596763563,0.119278963515,0.753735920203;0.119278963515,5.13855681906,0.37402442613;0.753735920203,0.37402442613,3.92921317227];
  constant Real frameMass = 10.0872 "kg";
  constant Real frameCOM[3] = {0.235,0.344967880086,0.460471092077};
  constant Real frameInertia[3,3] = [2.17137681096,-3.58868538878e-17,-1.38777878078e-16;-3.58868538878e-17,1.75901014137,-0.00205431263383;-1.38777878078e-16,-0.00205431263383,1.23792694959];
end CADParameters;
end Generated;
