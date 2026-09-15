model ProbeThermalContact
  "Diagnostic contact/stem network; parameters are not a qualified probe"
  parameter Real wallC=270;
  parameter Real ambientC=25;
  parameter Real contactConductance=1.215 "W/K assumed";
  parameter Real stemConductance=0.01 "W/K assumed";
  parameter Real heatCapacity=1 "J/K assumed";
  Real junctionC(start=ambientC, fixed=true);
equation
  heatCapacity*der(junctionC)=contactConductance*(wallC-junctionC)
                           -stemConductance*(junctionC-ambientC);
end ProbeThermalContact;
