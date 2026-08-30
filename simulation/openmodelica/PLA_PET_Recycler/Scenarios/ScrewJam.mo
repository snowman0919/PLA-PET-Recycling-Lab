within PLA_PET_Recycler.Scenarios;
model ScrewJam
  extends Systems.ThermalExtruderSystem(material=2,screwJammed=true);
  parameter String protectedRequirement="SYS-EX-JAM-01";
  parameter String estimatedParameters="binary mechanical jam; pressure sensor absent";
  parameter String acceptance="screw RPM zero and torque trip true while heaters remain bounded";
end ScrewJam;
