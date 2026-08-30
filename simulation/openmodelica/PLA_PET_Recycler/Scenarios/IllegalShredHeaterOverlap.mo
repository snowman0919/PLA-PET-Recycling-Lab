within PLA_PET_Recycler.Scenarios;
model IllegalShredHeaterOverlap
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.SHREDDING,illegalOverlapRequest=true);
  parameter String acceptance="hard arbiter rejects simultaneous shredder and process-heater request";
end IllegalShredHeaterOverlap;
