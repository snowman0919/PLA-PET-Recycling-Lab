within PLA_PET_Recycler.Components;
model SafetyController
  parameter Real jamStart=1e9;
  parameter Real retryPeriod=0.40;
  input Boolean permission;
  output Integer retryCount;
  output Boolean latchedFault;
  output Real commandSign;
equation
  retryCount = if time<jamStart then 0 else min(Parameters.maxReverseRetries,integer((time-jamStart)/retryPeriod)+1);
  latchedFault = (not permission) or time>=jamStart+Parameters.maxReverseRetries*retryPeriod;
  commandSign = if latchedFault then 0 else if retryCount>0 and mod(retryCount,2)==1 then -1 else 1;
end SafetyController;
