within PLA_PET_Recycler.Systems;
model FullMechanicalSystem
  ShredderSystem shredder;
  ExtruderSystem extruder;
  FormingSpoolSystem forming;
  Components.FrameMount frame;
  Real baseReaction;
  Real tippingMoment;
  Real anchorTension;
equation
  frame.processReaction=shredder.frameReaction+extruder.load.torque/0.10+forming.lineTension;
  baseReaction=frame.baseReaction;
  tippingMoment=frame.tippingMoment;
  anchorTension=frame.anchorTension;
end FullMechanicalSystem;
