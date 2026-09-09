within PLA_PET_Recycler.Scenarios;
package V08ReleaseScenarios
  model HotZoneControlledExpansion
    parameter Real barrelLengthM=0.280;
    parameter Real alphaPerK=17e-6;
    parameter Real ambientC=25;
    parameter Real petBulkC=270;
    parameter Real axialTravelMm=1.3;
    parameter Real regionalStressMPa=83.5;
    parameter Real allowableMPa=180;
    Real temperatureC(start=ambientC,fixed=true);
    Real axialGrowthMm;
    Real travelMarginMm;
    Real safetyFactor;
    Boolean pass;
  equation
    der(temperatureC)=(petBulkC-temperatureC)/60;
    axialGrowthMm=alphaPerK*(temperatureC-ambientC)*barrelLengthM*1000;
    travelMarginMm=axialTravelMm-axialGrowthMm;
    safetyFactor=allowableMPa/regionalStressMPa;
    pass=travelMarginMm>=0 and safetyFactor>=2;
    when terminal() then
      assert(pass,"hot-zone controlled-expansion contract failed");
    end when;
  end HotZoneControlledExpansion;

  model LC09SpoolScope
    parameter Real spindleLengthMm=143;
    parameter Real bearingSpacingMm=88;
    parameter Real loadPositionFromFrontMm=40.5;
    parameter Real spoolMassKg=1.35;
    parameter Real lineTensionN=8;
    parameter Real gravityMS2=9.80665;
    Real radialLoadN;
    Real frontReactionN;
    Real rearReactionN;
    Real forceResidualN;
    Real momentResidualNmm;
    Boolean scopePass;
  equation
    radialLoadN=spoolMassKg*gravityMS2+lineTensionN;
    rearReactionN=radialLoadN*loadPositionFromFrontMm/bearingSpacingMm;
    frontReactionN=radialLoadN-rearReactionN;
    forceResidualN=frontReactionN+rearReactionN-radialLoadN;
    momentResidualNmm=rearReactionN*bearingSpacingMm-radialLoadN*loadPositionFromFrontMm;
    scopePass=abs(spindleLengthMm-143)<1e-9 and abs(bearingSpacingMm-88)<1e-9 and
      abs(loadPositionFromFrontMm-40.5)<1e-9 and abs(forceResidualN)<1e-9 and abs(momentResidualNmm)<1e-9;
    when terminal() then
      assert(scopePass,"LC09 geometry/load scope contract failed");
    end when;
  end LC09SpoolScope;

  partial model SpoolDynamics
    "Mechanical/control surrogate: not compiled firmware or physical validation"
    parameter Real coreRadiusMm=26;
    parameter Real fullRadiusMm=100;
    parameter Real windingWidthMm=68 "Usable winding width, not 73 mm physical spool width";
    parameter Real packingFactor=0.87 "Current SpoolerConfig default";
    parameter Real filamentDiameterMm=1.75;
    parameter Real traversePitchMm=1.85;
    parameter Real lineSpeedMmS=9.28 "Current drive contract nominal PLA";
    parameter Real densityKgM3=1240 "Engineering assumed density, not measured lot data";
    parameter Real initialFill=0;
    parameter Boolean lockedSpindle=false;
    parameter Real jamObservationGraceS=1.5;
    parameter Boolean stopAtOneKg=true;
    Systems.DynamicSpoolSystem plant(
      lineSpeedCommand=lineSpeedMmS/1000,
      coreRadius=coreRadiusMm/1000,fullRadius=fullRadiusMm/1000,
      windingWidth=windingWidthMm/1000,fillFactor=packingFactor,
      filamentDiameter=filamentDiameterMm/1000,
      initialFill=initialFill,spoolJammed=lockedSpindle,
      useExternalEnable=true,externalEnable=not safePause,externalDemand=true);
    discrete Boolean faultLatched(start=false,fixed=true);
    discrete Boolean batchComplete(start=false,fixed=true);
    Boolean safePause;
    Boolean jamEligible;
    Real radiusMm;
    Real targetRpm;
    Real actualRpm;
    Real spoolTurns;
    Real traversePhaseMm;
    Real traversePositionMm;
    Real dancerAngleRad;
    Real hardStopMarginRad;
    Real addedMassKg;
    Real spoolCommandNm;
    Real volumeResidualM3;
  equation
    safePause=faultLatched;
    jamEligible=lockedSpindle and time>=jamObservationGraceS and plant.jamDetected;
    when plant.tensionFault or jamEligible then
      faultLatched=true;
    end when;
    when stopAtOneKg and addedMassKg>=1 then
      batchComplete=true;
      // End the material-fill experiment, not a claim of physical stopping.
      // DynamicSpoolSystem has no signed unwinding material model.
      terminate("One-kilogram material-fill experiment complete; stopping/unwinding not validated");
    end when;
    radiusMm=1000*plant.spoolRadius;
    targetRpm=plant.effectiveLineSpeed/(2*Modelica.Constants.pi*plant.spoolRadius)*60;
    actualRpm=plant.spoolSpeed*60/(2*Modelica.Constants.pi);
    spoolTurns=plant.spoolAngle/(2*Modelica.Constants.pi);
    traversePhaseMm=mod(max(0,spoolTurns)*traversePitchMm,2*windingWidthMm);
    traversePositionMm=if traversePhaseMm<=windingWidthMm then traversePhaseMm else 2*windingWidthMm-traversePhaseMm;
    dancerAngleRad=plant.dancerAngle;
    hardStopMarginRad=GeneratedControl.dancerHardStop-abs(dancerAngleRad);
    addedMassKg=plant.woundLength*plant.filamentArea*densityKgM3;
    spoolCommandNm=plant.motorTorque;
    // initialFill=1 cases intentionally freeze full-radius geometry: a short
    // worst-radius/inertia envelope, not a material-capacity prediction.
    volumeResidualM3=Modelica.Constants.pi*((radiusMm/1000)^2-(coreRadiusMm/1000)^2
      -initialFill*((fullRadiusMm/1000)^2-(coreRadiusMm/1000)^2))
      *(windingWidthMm/1000)*packingFactor-plant.woundLength*plant.filamentArea;
  end SpoolDynamics;

  model SpoolerTraverseEmptyToFull
    "Empty core to a one-kilogram PLA batch; volume-integrated radius"
    extends SpoolDynamics;
  end SpoolerTraverseEmptyToFull;

  model SpoolerPETOneKg
    extends SpoolDynamics(lineSpeedMmS=8.66,densityKgM3=1380);
  end SpoolerPETOneKg;

  model SpoolerFullRadiusPLA
    "100 mm radius / inherited full inertia boundary, not a 1 kg capacity claim"
    extends SpoolDynamics(initialFill=1,stopAtOneKg=false);
  end SpoolerFullRadiusPLA;

  model SpoolerFullRadiusPET
    extends SpoolDynamics(initialFill=1,stopAtOneKg=false,lineSpeedMmS=8.66,densityKgM3=1380);
  end SpoolerFullRadiusPET;

  model SpoolerJamContainment
    "Locked-spindle startup fault with explicit observation grace and latched pause"
    extends SpoolDynamics(lockedSpindle=true,stopAtOneKg=false);
  end SpoolerJamContainment;
end V08ReleaseScenarios;
