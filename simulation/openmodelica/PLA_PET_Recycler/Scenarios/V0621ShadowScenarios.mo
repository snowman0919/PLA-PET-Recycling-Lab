within PLA_PET_Recycler.Scenarios;
package V0621ShadowScenarios
  partial model TachShadow
    parameter Real targetRpm=5;
    parameter Integer ppr=6;
    parameter Real timeoutUs=2500000;
    parameter Real minimumPulseSpacingUs=20000;
    parameter Real filterTauS=0.25;
    parameter Real maximumAccelerationRpmS=120;
    parameter Real jitterFraction=0;
    parameter Boolean missingPulse=false;
    parameter Boolean rollover=false;
    Real nominalPulseIntervalUs;
    Real observedPulseIntervalUs;
    Real timestampDeltaSignedUs;
    Real timestampDeltaCorrectedUs;
    Real rawRpm;
    Real filteredRpm(start=0,fixed=true);
    Real estimateErrorRpm;
    Real pulseAgeUs;
    Boolean tachValid;
    Boolean duplicateRejected;
    Boolean reciprocalMode;
    Boolean rolloverHandled;
  equation
    nominalPulseIntervalUs=60e6/(ppr*targetRpm);
    observedPulseIntervalUs=nominalPulseIntervalUs*(1+jitterFraction)*
      (if missingPulse and time>=4 and time<6 then 2 else 1);
    timestampDeltaSignedUs=if rollover then observedPulseIntervalUs-4294967296.0 else observedPulseIntervalUs;
    timestampDeltaCorrectedUs=if timestampDeltaSignedUs<0 then timestampDeltaSignedUs+4294967296.0 else timestampDeltaSignedUs;
    rawRpm=60e6/(ppr*timestampDeltaCorrectedUs);
    der(filteredRpm)=max(-maximumAccelerationRpmS,min(maximumAccelerationRpmS,
      (rawRpm-filteredRpm)/filterTauS));
    estimateErrorRpm=filteredRpm-targetRpm;
    pulseAgeUs=if missingPulse and time>=4 and time<6 then observedPulseIntervalUs else nominalPulseIntervalUs;
    tachValid=pulseAgeUs<timeoutUs;
    duplicateRejected=minimumPulseSpacingUs<nominalPulseIntervalUs;
    reciprocalMode=targetRpm<=40;
    rolloverHandled=not rollover or abs(timestampDeltaCorrectedUs-observedPulseIntervalUs)<0.5;
  end TachShadow;

  model LowSpeedTachShredder
    extends TachShadow(targetRpm=V0621Contracts.shredderMinRpm,
      ppr=V0621Contracts.shredderPpr,timeoutUs=V0621Contracts.shredderTimeoutUs,
      minimumPulseSpacingUs=V0621Contracts.shredderMinPulseSpacingUs,
      filterTauS=V0621Contracts.shredderFilterTauS,
      maximumAccelerationRpmS=V0621Contracts.shredderMaxAccelRpmS);
  end LowSpeedTachShredder;
  model LowSpeedTachScrew
    extends TachShadow(targetRpm=V0621Contracts.screwMinRpm,
      ppr=V0621Contracts.screwPpr,timeoutUs=V0621Contracts.screwTimeoutUs,
      minimumPulseSpacingUs=V0621Contracts.screwMinPulseSpacingUs,
      filterTauS=V0621Contracts.screwFilterTauS,
      maximumAccelerationRpmS=V0621Contracts.screwMaxAccelRpmS);
  end LowSpeedTachScrew;
  model LowSpeedTachPuller
    extends TachShadow(targetRpm=V0621Contracts.pullerMinRpm,
      ppr=V0621Contracts.pullerPpr,timeoutUs=V0621Contracts.pullerTimeoutUs,
      minimumPulseSpacingUs=V0621Contracts.pullerMinPulseSpacingUs,
      filterTauS=V0621Contracts.pullerFilterTauS,
      maximumAccelerationRpmS=V0621Contracts.pullerMaxAccelRpmS);
  end LowSpeedTachPuller;
  model LowSpeedTachSpooler
    extends TachShadow(targetRpm=V0621Contracts.spoolerMinRpm,
      ppr=V0621Contracts.spoolerPpr,timeoutUs=V0621Contracts.spoolerTimeoutUs,
      minimumPulseSpacingUs=V0621Contracts.spoolerMinPulseSpacingUs,
      filterTauS=V0621Contracts.spoolerFilterTauS,
      maximumAccelerationRpmS=V0621Contracts.spoolerMaxAccelRpmS);
  end LowSpeedTachSpooler;
  model TachJitter
    extends TachShadow(targetRpm=V0621Contracts.screwCrossoverRpm,
      ppr=V0621Contracts.screwPpr,timeoutUs=V0621Contracts.screwTimeoutUs,
      minimumPulseSpacingUs=V0621Contracts.screwMinPulseSpacingUs,
      filterTauS=V0621Contracts.screwFilterTauS,
      maximumAccelerationRpmS=V0621Contracts.screwMaxAccelRpmS,jitterFraction=0.08);
  end TachJitter;
  model TachMissingPulse
    extends TachShadow(targetRpm=V0621Contracts.pullerNormalMaxRpm,
      ppr=V0621Contracts.pullerPpr,timeoutUs=V0621Contracts.pullerTimeoutUs,
      minimumPulseSpacingUs=V0621Contracts.pullerMinPulseSpacingUs,
      filterTauS=V0621Contracts.pullerFilterTauS,
      maximumAccelerationRpmS=V0621Contracts.pullerMaxAccelRpmS,missingPulse=true);
  end TachMissingPulse;
  model TachRollover
    extends TachShadow(targetRpm=32,ppr=V0621Contracts.shredderPpr,
      timeoutUs=V0621Contracts.shredderTimeoutUs,
      minimumPulseSpacingUs=V0621Contracts.shredderMinPulseSpacingUs,
      filterTauS=V0621Contracts.shredderFilterTauS,
      maximumAccelerationRpmS=V0621Contracts.shredderMaxAccelRpmS,rollover=true);
  end TachRollover;

  partial model DriveClosedLoopShadow
    parameter Real targetRpm=16;
    parameter Real maximumRpm=25;
    parameter Real minimumStableRpm=1;
    parameter Real loadStepRpm=2;
    parameter Real loadStart=4;
    parameter Real loadEnd=8;
    parameter Real tachLossAt=1e9;
    parameter Real kp=1.8;
    parameter Real ki=1.2;
    parameter Real antiWindup=0.8;
    parameter Real motorTauS=0.45;
    parameter Real pwmDeadZone=0.15;
    Real actualRpm(start=0,fixed=true);
    Real speedErrorRpm;
    Real speedIntegrator(start=0,fixed=true);
    Real unconstrainedCommandRpm;
    Real commandRpm;
    Real pwmFraction;
    Real appliedLoadRpm;
    Boolean saturated;
    Boolean tachValid;
    Boolean controlledRundown;
    Boolean continuousRegion;
    Real cutterTorqueNm;
    Real phaseTorqueNm;
    Real bearingLoadN;
    Real chainForceN;
  equation
    tachValid=time<tachLossAt;
    controlledRundown=not tachValid;
    speedErrorRpm=(if tachValid then targetRpm-actualRpm else 0);
    unconstrainedCommandRpm=(if tachValid then targetRpm+kp*speedErrorRpm+ki*speedIntegrator else 0);
    commandRpm=max(0,min(maximumRpm,unconstrainedCommandRpm));
    saturated=unconstrainedCommandRpm<0 or unconstrainedCommandRpm>maximumRpm;
    der(speedIntegrator)=speedErrorRpm+antiWindup*(commandRpm-unconstrainedCommandRpm);
    appliedLoadRpm=if time>=loadStart and time<loadEnd then loadStepRpm else 0;
    der(actualRpm)=(max(0,commandRpm-appliedLoadRpm)-actualRpm)/motorTauS;
    pwmFraction=if commandRpm>0 then pwmDeadZone+(1-pwmDeadZone)*commandRpm/maximumRpm else 0;
    continuousRegion=targetRpm>=minimumStableRpm and targetRpm<=0.85*maximumRpm;
    cutterTorqueNm=if time>=loadStart and time<loadEnd then V0621Contracts.cutterEnvelopeNm else 12;
    phaseTorqueNm=if time>=loadStart and time<loadEnd then V0621Contracts.phaseEnvelopeNm else 8;
    bearingLoadN=if time>=loadStart and time<loadEnd then V0621Contracts.bearingEnvelopeN else 800;
    chainForceN=if time>=loadStart and time<loadEnd then V0621Contracts.chainEnvelopeN else 250;
  end DriveClosedLoopShadow;

  model ShredderClosedLoopLoadStep
    extends DriveClosedLoopShadow(targetRpm=V0621Contracts.shredderNormalRpm,
      maximumRpm=V0621Contracts.shredderMaxRpm,
      minimumStableRpm=V0621Contracts.shredderMinRpm,loadStepRpm=5);
  end ShredderClosedLoopLoadStep;
  model ScrewClosedLoopPressureStep
    extends DriveClosedLoopShadow(targetRpm=V0621Contracts.screwNormalRpm,
      maximumRpm=V0621Contracts.screwMaxRpm,
      minimumStableRpm=V0621Contracts.screwMinRpm,loadStepRpm=2);
  end ScrewClosedLoopPressureStep;
  model PullerClosedLoopLowSpeed
    extends DriveClosedLoopShadow(targetRpm=V0621Contracts.pullerNormalMinRpm,
      maximumRpm=V0621Contracts.pullerControllableMaxRpm,
      minimumStableRpm=V0621Contracts.pullerControllableMinRpm,loadStepRpm=0.6);
  end PullerClosedLoopLowSpeed;
  model ActuatorDeadZoneRecovery
    extends DriveClosedLoopShadow(targetRpm=V0621Contracts.pullerNormalMinRpm,
      maximumRpm=V0621Contracts.pullerControllableMaxRpm,
      minimumStableRpm=V0621Contracts.pullerControllableMinRpm,
      loadStepRpm=0,pwmDeadZone=V0621Contracts.pullerPwmDeadZoneFraction);
  end ActuatorDeadZoneRecovery;
  model ActuatorSaturationRecovery
    extends DriveClosedLoopShadow(targetRpm=16,maximumRpm=25,minimumStableRpm=1,
      loadStepRpm=18,loadStart=4,loadEnd=7);
  end ActuatorSaturationRecovery;
  model ActuatorTachLossRundown
    extends DriveClosedLoopShadow(targetRpm=16,maximumRpm=25,minimumStableRpm=1,
      loadStepRpm=0,tachLossAt=5);
  end ActuatorTachLossRundown;

  model SpoolerClosedLoopEmptyToFull
    parameter Real lineSpeedMmS=9.28;
    parameter Real filamentDiameterMm=1.75;
    parameter Real windingWidthMm=68;
    parameter Real coreRadiusMm=26;
    parameter Real fullRadiusMm=100;
    parameter Real packingFactor=0.82;
    Real actualWoundLengthMm;
    Real fullLengthMm;
    Real estimatedRadiusMm;
    Real targetRpm;
    Real actualRpm(start=0,fixed=true);
    Real speedErrorRpm;
    Real commandRpm;
    Boolean radiusBounded;
    Boolean continuousRegion;
  equation
    fullLengthMm=4*packingFactor*windingWidthMm*(fullRadiusMm^2-coreRadiusMm^2)/(filamentDiameterMm^2);
    actualWoundLengthMm=fullLengthMm*min(time/16,1);
    estimatedRadiusMm=min(fullRadiusMm,max(coreRadiusMm,
      sqrt(coreRadiusMm^2+actualWoundLengthMm*filamentDiameterMm^2/(4*packingFactor*windingWidthMm))));
    targetRpm=lineSpeedMmS*60/(2*Modelica.Constants.pi*estimatedRadiusMm);
    speedErrorRpm=targetRpm-actualRpm;
    commandRpm=max(0,min(V0621Contracts.spoolerControllableMaxRpm,targetRpm+1.4*speedErrorRpm));
    der(actualRpm)=(commandRpm-actualRpm)/0.5;
    radiusBounded=estimatedRadiusMm>=coreRadiusMm and estimatedRadiusMm<=fullRadiusMm;
    continuousRegion=targetRpm>=V0621Contracts.spoolerControllableMinRpm and
      targetRpm<=0.85*V0621Contracts.spoolerControllableMaxRpm;
  end SpoolerClosedLoopEmptyToFull;

  partial model TraverseHomingShadow
    parameter Boolean wrongDirection=false;
    parameter Boolean leftLimitHealthy=true;
    parameter Real initialPositionMm=34;
    Real traversePositionMm;
    Integer homingState;
    Boolean directionPlausible;
    Boolean leftLimit;
    Boolean traverseReady;
    Boolean traverseFault;
  equation
    traversePositionMm=if wrongDirection then min(68,initialPositionMm+8*time)
      else if not leftLimitHealthy then max(0,initialPositionMm-8*time)
      else if time<initialPositionMm/8 then initialPositionMm-8*time
      else if time<initialPositionMm/8+0.5 then 4*(time-initialPositionMm/8)
      else 2;
    directionPlausible=not wrongDirection;
    leftLimit=leftLimitHealthy and not wrongDirection and time>=initialPositionMm/8;
    traverseFault=wrongDirection and time>=1 or not leftLimitHealthy and time>=6;
    traverseReady=leftLimit and time>=initialPositionMm/8+0.5 and not traverseFault;
    homingState=if traverseFault then 6 else if traverseReady then 4
      else if leftLimit then 3 else 2;
  end TraverseHomingShadow;
  model TraverseHomeMiddle
    extends TraverseHomingShadow;
  end TraverseHomeMiddle;
  model TraverseHomeWrongDirection
    extends TraverseHomingShadow(wrongDirection=true);
  end TraverseHomeWrongDirection;
  model TraverseLimitFailure
    extends TraverseHomingShadow(leftLimitHealthy=false);
  end TraverseLimitFailure;

  partial model RecirculationShadow
    parameter Boolean petRibbon=false;
    Real oversizeReturnProbability;
    Real ribbonBypassProbability;
    Real deadPocketProbability;
    Real axialMigrationProbability;
    Real cutterTorqueNm;
    Boolean guardedFragmentEjection;
    Boolean passes;
  equation
    oversizeReturnProbability=V0621Contracts.recirculationReturnProbability;
    ribbonBypassProbability=if petRibbon then V0621Contracts.ribbonBypassProbability else 0;
    deadPocketProbability=V0621Contracts.deadPocketProbability;
    axialMigrationProbability=V0621Contracts.axialMigrationProbability;
    cutterTorqueNm=V0621Contracts.cutterEnvelopeNm;
    guardedFragmentEjection=false;
    passes=oversizeReturnProbability>=0.9 and ribbonBypassProbability<=0.01 and
      deadPocketProbability<=0.02 and axialMigrationProbability<=0.01 and not guardedFragmentEjection;
  end RecirculationShadow;
  model PLAShredderRecirculation
    extends RecirculationShadow(petRibbon=false);
  end PLAShredderRecirculation;
  model PETRibbonRecirculation
    extends RecirculationShadow(petRibbon=true);
  end PETRibbonRecirculation;

  partial model FeedInventoryShadow
    parameter Real deliveredNominalGH=100;
    parameter Real bridgeClearTimeS=0;
    parameter Boolean degraded=false;
    parameter Boolean safePause=false;
    Real deliveredFeedGH;
    Real feedInventoryG(start=V0621Contracts.feedInventoryTargetG,fixed=true);
    Real continuousStarvationS;
    Real bridgeClearCycles;
    Real feederTorqueNm;
    Real feederCurrentA;
    Real attachmentReactionTorqueNm;
    Real attachmentVerticalLoadN;
    Boolean uncontrolledOverfeed;
    Boolean controlledPause;
    Boolean inventoryBounded;
  equation
    deliveredFeedGH=if time<bridgeClearTimeS then 0 else if degraded then 75 else deliveredNominalGH;
    der(feedInventoryG)=(deliveredFeedGH-(if time<bridgeClearTimeS then 0 else deliveredFeedGH))/3600;
    continuousStarvationS=if time<bridgeClearTimeS then time else 0;
    bridgeClearCycles=if bridgeClearTimeS>0 then 2 else 0;
    feederTorqueNm=if degraded then 2.05 else 1.4132270676691736;
    feederCurrentA=if degraded then 3.74 else 2.768105142857144;
    attachmentReactionTorqueNm=2.2;
    attachmentVerticalLoadN=5.4;
    uncontrolledOverfeed=deliveredFeedGH>V0621Contracts.feedNormalMaxGH and not controlledPause;
    controlledPause=safePause or degraded;
    inventoryBounded=feedInventoryG>=0 and feedInventoryG<=V0621Contracts.feedInventoryCapacityG;
  end FeedInventoryShadow;
  model PLAHopperBridgeClear
    extends FeedInventoryShadow(deliveredNominalGH=V0621Contracts.feedNominalMinObservedGH,bridgeClearTimeS=1.5);
  end PLAHopperBridgeClear;
  model PETHopperBridgeClear
    extends FeedInventoryShadow(deliveredNominalGH=V0621Contracts.feedNominalMinObservedGH,bridgeClearTimeS=2.0);
  end PETHopperBridgeClear;
  model FeedRateNominalPLA
    extends FeedInventoryShadow(deliveredNominalGH=V0621Contracts.feedNominalMaxObservedGH);
  end FeedRateNominalPLA;
  model FeedRateNominalPET
    extends FeedInventoryShadow(deliveredNominalGH=V0621Contracts.feedNominalMinObservedGH);
  end FeedRateNominalPET;
  model FeedRateDegradedSafePause
    extends FeedInventoryShadow(deliveredNominalGH=75,degraded=true,safePause=true);
  end FeedRateDegradedSafePause;
end V0621ShadowScenarios;
