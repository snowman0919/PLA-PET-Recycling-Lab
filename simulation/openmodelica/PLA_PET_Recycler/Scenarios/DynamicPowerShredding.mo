within PLA_PET_Recycler.Scenarios;
model DynamicPowerShredding
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.SHREDDING);
end DynamicPowerShredding;
