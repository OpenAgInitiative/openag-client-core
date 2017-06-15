/**
 *  \file openag_binary_sensor.cpp
 *  \brief Binary Sensor for OpenAg brain.
 */
/***************************************************

 ****************************************************/
#include "openag_binary_sensor.h"

BinarySensor::BinarySensor(int pin, bool is_active_low) {
  _pin = pin;
  _is_active_low = is_active_low;
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
}

uint8_t BinarySensor::begin() {
  pinMode(_pin, INPUT);
  _is_on = false;
  _time_of_last_reading = 0;
  return status_level;
}

uint8_t BinarySensor::update() {
  if (millis() - _time_of_last_reading > _min_update_interval) {
    readData();
    _time_of_last_reading = millis();
  }
  return status_level;
}

bool BinarySensor::get_is_on() {
  return _is_on;
}

void BinarySensor::readData() {
  _is_on = digitalRead(_pin) ^ _is_active_low;
}
