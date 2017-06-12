/**
 *  \file openag_ds18b20.cpp
 *  \brief Sensor module for temperature.
 */
#include "openag_ds18b20.h"

Ds18b20::Ds18b20(int pin) : _oneWire(pin) {
  _sensors = DallasTemperature(&_oneWire);
  _sensors.setWaitForConversion(false);
}

uint8_t Ds18b20::begin() {
  _sensors.begin();
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  _waiting_for_conversion = false;
  _time_of_last_query = 0;
  if (!_sensors.getAddress(_address, 0)) {
    status_level = ERROR;
    status_code = CODE_COULDNT_FIND_ADDRESS;
    status_msg = "Unable to find address for sensor";
  }
  return status_level;
}

uint8_t Ds18b20::update() {
  if (_waiting_for_conversion) {
    if (_sensors.isConversionComplete()) {
      status_level = OK;
      status_code = CODE_OK;
      status_msg = "";
      _waiting_for_conversion = false;
      _temperature = _sensors.getTempC(_address);
      _send_temperature = true;
    }
    else if (millis() - _time_of_last_query > _min_update_interval) {
      status_level = ERROR;
      status_code = CODE_NO_RESPONSE;
      status_msg = "Sensor isn't responding to queries";
    }
  }
  if (millis() - _time_of_last_query > _min_update_interval) {
    _sensors.requestTemperatures();
    _waiting_for_conversion = true;
    _time_of_last_query = millis();
  }
  return status_code;
}

float Ds18b20::get_temperature() {
  return _temperature;
}
