within PLA_PET_Recycler;
package Generated
package CADParameters
  constant String revision = "virtual-physics-closure-v0.5.1";
  constant String baselineSHA256 = "28532bb5439a1749c34e643f173d18d13bacd882b99b4bd557e0357ba92956b0";
  constant Real cutterDiscMass = 0.0684185363429 "kg";
  constant Real cutterRotorMass = 1.1752119536 "kg";
  constant Real cutterRotorJ = 0.000255685606089 "kg.m2";
  constant Real screwMass = 0.30789075164 "kg";
  constant Real screwJ = 6.51334629861e-06 "kg.m2";
  constant Real cutterSprocketRadius = 0.0364869297035 "m";
  constant Real motorSprocketRadius = 0.0184008869908 "m";
  constant Real phaseGearRadius = 0.024 "m";
  constant Real shaftCenters[2,3] = [0.105,0,0.590;0.153,0,0.590] "m";
  constant Real bearingCenters[4,3] = [0.105,0.315,0.590;0.105,0.455,0.590;0.153,0.315,0.590;0.153,0.455,0.590] "m";
  constant Real spoolEmptyJ = 0.0018683 "kg.m2";
  constant Real spoolFullJ = 0.0072063 "kg.m2";
  constant Real assemblyMass = 70.9437825359 "kg";
  constant Real assemblyCOM[3] = {0.262723366182,0.363751937556,0.382917865829};
  constant Real assemblyInertia[3,3] = [7.33508144414,-0.082974505603,0.647218377768;-0.082974505603,6.39711125298,0.352077934347;0.647218377768,0.352077934347,4.19729080195];
  constant Real frameMass = 25.5008 "kg";
  constant Real frameCOM[3] = {0.248817919438,0.367713765843,0.38688292132};
  constant Real frameInertia[3,3] = [3.9629894641,-0.0427729077576,0.0621685212197;-0.0427729077576,3.48008705035,0.155081760181;0.0621685212197,0.155081760181,2.46357184182];
end CADParameters;
end Generated;
