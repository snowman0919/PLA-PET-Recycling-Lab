within PLA_PET_Recycler;
package Generated
package CADParameters
  constant String revision = "solid-manifold-openmodelica-v0.4";
  constant String baselineSHA256 = "eb6e282411a12d33b7de3590b22a7ddc259bf85f2b08843eefd62a24cced069c";
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
  constant Real assemblyMass = 73.5155915676 "kg";
  constant Real assemblyCOM[3] = {0.255968130122,0.348910816846,0.392927757752};
  constant Real assemblyInertia[3,3] = [7.95604088529,-0.199302251868,0.782955799558;-0.199302251868,6.76614794421,0.705333224108;0.782955799558,0.705333224108,4.3521032077];
  constant Real frameMass = 24.0768 "kg";
  constant Real frameCOM[3] = {0.249635167464,0.372190457204,0.36355927698};
  constant Real frameInertia[3,3] = [3.93371969164,-0.0411954649761,0.053950015311;-0.0411954649761,3.42472953951,0.173735969421;0.053950015311,0.173735969421,2.29630470275];
end CADParameters;
end Generated;
