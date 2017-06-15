/**
 *  \file openag_ds18b20.h
 *  \brief Sensor module for temperature.
 */
#ifndef DS18B20_H
#define DS18B20_H

#if ARDUINO >= 100
 #include <Arduino.h>
#else
 #include "WProgram.h"
#endif

#include <OneWire.h>
#include <DallasTemperature.h>
#include <openag_module.h>

/**
 * \brief Sensor module for temperature
 */
class Ds18b20 : public Module {
  public:
    Ds18b20(int pin);
    uint8_t begin();
    uint8_t update();
    float get_temperature();

  private:
    OneWire _oneWire;
    DeviceAddress _address;
    DallasTemperature _sensors;
    bool _send_temperature;
    float _temperature;
    uint32_t _time_of_last_query;
    bool _waiting_for_conversion;
    const static uint32_t _min_update_interval = 2000;

    // Status codes
    static const uint8_t CODE_COULDNT_FIND_ADDRESS = 1;
    static const uint8_t CODE_NO_RESPONSE = 2;
};

#endif
