within PLA_PET_Recycler;
package Parameters
  constant String revision = "coupled-digital-validation-v0.5";
  constant Real normalTorque = 14 "N.m";
  constant Real electricalTripTorque = 18 "N.m";
  constant Real inputFuseTorque = 22 "N.m";
  constant Real phaseAllowableTorque = 34 "N.m";
  constant Real shaftAllowableTorque = 48 "N.m";
  constant Real phaseErrorLimit = 0.0174532925199433 "rad, geometry-derived 1 degree digital allowance";
  constant Integer maxReverseRetries = 3;
  constant Real reverseDuration = 0.30 "s digital controller replica";
  constant Real lineTensionLimit = 8 "N";
  constant Real screwRPMPLA = 18;
  constant Real screwRPMPET = 20;
  constant Real throughputPerRPMPLA = 6.211 "g/h/rpm nominal";
  constant Real throughputPerRPMPET = 5.420 "g/h/rpm nominal";
end Parameters;
