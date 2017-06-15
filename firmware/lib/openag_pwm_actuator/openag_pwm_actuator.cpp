#include "openag_pwm_actuator.h"

PwmActuator::PwmActuator(int pin, bool is_active_low, float threshold) {
  _pin = pin;
  _is_active_low = is_active_low;
  _threshold = threshold;
  _last_cmd = 0;
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
}

uint8_t PwmActuator::begin() {
  pinMode(_pin, OUTPUT);
  if (_is_active_low) {
    digitalWrite(_pin, HIGH);
  }
  else {
    digitalWrite(_pin, LOW);
  }
  return status_level;
}

uint8_t PwmActuator::update() {
  uint32_t curr_time = millis();
  if ((curr_time - _last_cmd) > _max_update_interval) {
    if (_is_active_low) {
      analogWrite(_pin, 255);
    }
    else {
      analogWrite(_pin, 0);
    }
  }
  return status_level;
}

uint8_t PwmActuator::set_cmd(float cmd) {
  _last_cmd = millis();
  float val = cmd;
  if (val < 0 || val > 1) {
    status_level = WARN;
    status_code = CODE_INVALID_COMMAND;
    status_msg = "Invalid command received";
    return status_level;
  }
  else {
    status_level = OK;
    status_code = OK;
    status_msg = "";
  }
  val = _threshold + (1-_threshold)*val;
  if (_is_active_low) {
    val = 1-val;
  }
  int pwm_value = val*255;
  analogWrite(_pin, pwm_value);
  return status_level;
}
