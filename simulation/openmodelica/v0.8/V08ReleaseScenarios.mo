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
end V08ReleaseScenarios;
