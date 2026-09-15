#include <cassert>
#include <cmath>
#include <iostream>
#include "heater_control.h"

int main() {
  HeaterController plant;
  float temperature = 25.0f;
  for (uint32_t ms=250; ms<=2400000; ms+=250) {
    const TemperatureReading input{temperature,true,false,ms};
    const auto request=plant.update(0,input,245.0f,true,true,true,ms);
    const auto out=plant.applyAllocation(0,request.duty_percent,ms);
    assert(out.fault_bits==0 && out.duty_percent>=0 && out.duty_percent<=100);
    temperature+=0.25f*(out.allocated_duty_percent-0.30f*(temperature-25.0f))/100.0f;
  }
  assert(std::fabs(temperature-245.0f)<1.0f);
  HeaterController hold;
  for (uint32_t ms=250; ms<=400000; ms+=250) {
    const TemperatureReading input{ms<=10000 ? 25.0f : 244.0f,true,false,ms};
    const auto request=hold.update(0,input,245.0f,true,true,true,ms);
    const auto out=hold.applyAllocation(0,request.duty_percent,ms);
    assert(out.fault_bits==0 && out.duty_percent<=100);
  }
  HeaterController stalled;
  HeaterOutput output{};
  for (uint32_t ms=250; ms<=120500; ms+=250) {
    const TemperatureReading input{25.0f,true,false,ms};
    output=stalled.update(0,input,245.0f,true,true,true,ms);
  }
  assert((output.fault_bits&HEATER_NOT_HEATING)!=0 && output.duty_percent==0);
  HeaterController overtemp;
  const TemperatureReading hot{285.0f,true,false,1};
  output=overtemp.update(0,hot,245.0f,true,true,true,1);
  assert((output.fault_bits&HEATER_OVERTEMPERATURE)!=0 && output.duty_percent==0);
  HeaterController lost_permission;
  const TemperatureReading cold{25.0f,true,false,1};
  output=lost_permission.update(0,cold,245.0f,false,true,false,1);
  assert(output.duty_percent==0);
  std::cout << "HEATER_TRACKING_AND_WARMUP_WATCH_PASS cases=5\n";
}
