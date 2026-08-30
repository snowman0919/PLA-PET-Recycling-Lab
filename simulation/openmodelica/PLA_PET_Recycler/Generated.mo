within PLA_PET_Recycler;
package Generated
package CADParameters
  constant String revision = "safety-orchestration-closure-v0.6.1";
  constant String baselineSHA256 = "1fd09206bc13289febe49647bcac55c6d3bf54c2fae6f36bdc10399a0c8304e6";
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
  constant Real assemblyMass = 70.9437883795 "kg";
  constant Real assemblyCOM[3] = {0.262723361427,0.363751937103,0.382917865754};
  constant Real assemblyInertia[3,3] = [7.33508144433,-0.0829745074589,0.647218377459;-0.0829745074589,6.39711129439,0.352077934317;0.647218377459,0.352077934317,4.19729084352];
  constant Real frameMass = 25.5008 "kg";
  constant Real frameCOM[3] = {0.248817919438,0.367713765843,0.38688292132};
  constant Real frameInertia[3,3] = [3.9629894641,-0.0427729077576,0.0621685212197;-0.0427729077576,3.48008705035,0.155081760181;0.0621685212197,0.155081760181,2.46357184182];
end CADParameters;
end Generated;
