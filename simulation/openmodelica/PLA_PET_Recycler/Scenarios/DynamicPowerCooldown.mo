within PLA_PET_Recycler.Scenarios;
model DynamicPowerCooldown
  extends Systems.ProcessArbitrationSystem(initialState=GeneratedControl.COOLDOWN);
end DynamicPowerCooldown;
