#include "openag_mhz16.h"

MHZ16::MHZ16(int i2c_address) : _sensor(i2c_address) {
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  _send_air_carbon_dioxide = false;
  _time_of_last_reading = 0;
  _time_of_last_power_cycle = 0;
}

uint8_t MHZ16::begin() {
  _sensor.power_on();
  _is_on = true;
  if (!_sensor.begin()) {
    status_level = ERROR;
    status_code = CODE_FAILED_TO_INITIALIZE;
    status_msg = "Failed to initialize sensor";
  }
  else {
    status_level = WARN;
    status_code = CODE_INITIALIZING;
    status_msg = "Initializing";
    _init_time = millis();
    _initializing = true;
  }
  return status_level;
}

uint8_t MHZ16::update() {
  _send_air_carbon_dioxide = false;
  uint32_t curr_time = millis();
  // Handle clock rollover
  if (_time_of_last_power_cycle > curr_time || _time_of_last_reading > curr_time) {
    _time_of_last_reading = 0;
    _sensor.power_off();
    _is_on = false;
    _time_of_last_power_cycle = curr_time;
    status_level = WARN;
    status_code = CODE_INTENTIONAL_POWER_OFF;
    status_msg = "Powered off to prevent autocalibration";
    return status_level;
  }
  // Turn the sensor back on if it's been off for a while
  if (!_is_on) {
    if (curr_time - _time_of_last_power_cycle > _leave_off_for) {
      begin();
    }else{
      status_level = WARN;
      status_code = CODE_INTENTIONAL_POWER_OFF;
      status_msg = "Powered off to prevent autocalibration";
      return status_level;
    }
  }
  // Wait 10 seconds for initialization
  if (_initializing) {
    if (curr_time - _init_time < 10000) {
      return status_level;
    }
    else {
      _initializing = false;
      status_level = OK;
      status_code = CODE_OK;
      status_msg = "";
    }
  }
  // Turn off the sensor every once in a while
  if (curr_time - _time_of_last_power_cycle > _power_cycle_interval) {
    _sensor.power_off();
    _is_on = false;
    _time_of_last_power_cycle = curr_time;
    status_level = WARN;
    status_code = CODE_INTENTIONAL_POWER_OFF;
    status_msg = "Powered off to prevent autocalibration";
    return status_level;
  }
  // Read from the sensor
  if (curr_time - _time_of_last_reading > _min_update_interval) {
    if (_sensor.measure()) {
      if (status_level == OK) {
        _send_air_carbon_dioxide = true;
      }
      else {
        begin();
      }
    }
    else {
      if (status_level != ERROR) {
        status_level = ERROR;
        status_code = CODE_FAILED_TO_READ;
        status_msg = "Failed to read from sensor";
      }
      begin();
    }
    _time_of_last_reading = millis();
  }
  return status_level;
}

int MHZ16::get_air_carbon_dioxide() {
  return _sensor.ppm;
}
