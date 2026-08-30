within PLA_PET_Recycler.Scenarios;
model SensorOpen
  extends Systems.ThermalExtruderSystem(material=2,sensorOpen=true);
  parameter String protectedRequirement="SYS-THERM-FAULT-01";
  parameter String estimatedParameters="all-channel conservative open sensor fault";
  parameter String acceptance="all heater duties and screw RPM are zero";
end SensorOpen;
