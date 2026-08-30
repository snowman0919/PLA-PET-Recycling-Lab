within PLA_PET_Recycler.Systems;
model ProcessArbitrationSystem
  parameter Integer initialState=GeneratedControl.IDLE;
  parameter Integer nextState=initialState;
  parameter Real transitionTime=1e9;
  parameter Boolean illegalOverlapRequest=false;
  discrete Integer processState(start=initialState,fixed=true);
  Boolean requestedShredder;
  Boolean requestedHeater;
  Boolean shredderEnabled;
  Boolean screwEnabled;
  Boolean processHeaterEnabled;
  Boolean coolingEnabled;
  Boolean overlapBlocked;
  Real phaseAveragePower;
  Real phasePeakPower;
  Real psuCurrent;
  Real remainingWattMargin;
  Real remainingAmpereMargin;
  Boolean powerBudgetSafe;
equation
  when time>=transitionTime then
    processState=nextState;
  end when;
  requestedShredder=GeneratedControl.permissions[processState,1] or illegalOverlapRequest;
  requestedHeater=GeneratedControl.permissions[processState,3] or illegalOverlapRequest;
  shredderEnabled=requestedShredder and processState==GeneratedControl.SHREDDING;
  processHeaterEnabled=requestedHeater and not shredderEnabled;
  screwEnabled=GeneratedControl.permissions[processState,2] and not shredderEnabled;
  coolingEnabled=GeneratedControl.permissions[processState,7];
  overlapBlocked=not (shredderEnabled and (screwEnabled or processHeaterEnabled));
  phaseAveragePower=if processState==GeneratedControl.SHREDDING then GeneratedControl.phaseAverage[1] else if processState==GeneratedControl.PREHEATING then GeneratedControl.phaseAverage[2] else if processState==GeneratedControl.EXTRUSION then GeneratedControl.phaseAverage[3] else if processState==GeneratedControl.COOLDOWN then GeneratedControl.phaseAverage[4] else 0;
  phasePeakPower=if processState==GeneratedControl.SHREDDING then GeneratedControl.phasePeak[1] else if processState==GeneratedControl.PREHEATING then GeneratedControl.phasePeak[2] else if processState==GeneratedControl.EXTRUSION then GeneratedControl.phasePeak[3] else if processState==GeneratedControl.COOLDOWN then GeneratedControl.phasePeak[4] else 0;
  psuCurrent=phasePeakPower/24;
  remainingWattMargin=GeneratedControl.psuRating-phasePeakPower;
  remainingAmpereMargin=remainingWattMargin/24;
  powerBudgetSafe=phasePeakPower<=GeneratedControl.normalPhasePeakLimit and remainingWattMargin>=100;
end ProcessArbitrationSystem;
