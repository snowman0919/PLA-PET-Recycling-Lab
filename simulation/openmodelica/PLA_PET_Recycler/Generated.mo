within PLA_PET_Recycler;
package Generated
package CADParameters
  constant String revision = "final-design-fabrication-closure-v0.8";
  constant String baselineSHA256 = "eecde1249c65d84c499f7ab949a05ebbcb7fbd8dfa49d762d15d1eba24db304a";
  constant Real cutterDiscMass = 0.0605277466479 "kg";
  constant Real cutterRotorMass = 1.42370480027 "kg";
  constant Real cutterRotorJ = 0.000284882157782 "kg.m2";
  constant Real screwMass = 0.324759219243 "kg";
  constant Real screwJ = 8.10319960142e-06 "kg.m2";
  constant Real cutterSprocketRadius = 0.0364869297035 "m";
  constant Real motorSprocketRadius = 0.0184008869908 "m";
  constant Real phaseGearRadius = 0.024 "m";
  constant Real shaftCenters[2,3] = [0.105,0,0.590;0.153,0,0.590] "m";
  constant Real bearingCenters[4,3] = [0.105,0.315,0.590;0.105,0.455,0.590;0.153,0.315,0.590;0.153,0.455,0.590] "m";
  constant Real spoolEmptyJ = 0.0018683 "kg.m2";
  constant Real spoolFullJ = 0.0072063 "kg.m2";
  constant Real assemblyMass = 72.2155391098 "kg";
  constant Real assemblyCOM[3] = {0.265176227106,0.359153742189,0.386034825956};
  constant Real assemblyInertia[3,3] = [7.42940911907,-0.0661297823577,0.558025482487;-0.0661297823577,6.49161967693,0.409053059984;0.558025482487,0.409053059984,4.24289205832];
  constant Real frameMass = 25.5008 "kg";
  constant Real frameCOM[3] = {0.248817919438,0.367713765843,0.38688292132};
  constant Real frameInertia[3,3] = [3.9629894641,-0.0427729077576,0.0621685212197;-0.0427729077576,3.48008705035,0.155081760181;0.0621685212197,0.155081760181,2.46357184182];
end CADParameters;
end Generated;
