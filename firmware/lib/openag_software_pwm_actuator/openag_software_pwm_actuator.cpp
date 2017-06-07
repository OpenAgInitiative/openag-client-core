#include "openag_software_pwm_actuator.h"

SoftwarePwmActuator::SoftwarePwmActuator(int pin, bool is_active_low, int period) {
  _pin = pin;
  _is_active_low = is_active_low;
  _period = period;
  _duty_cycle = 0;
  _last_cmd = 0;
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
}

void SoftwarePwmActuator::begin() {
  pinMode(_pin, OUTPUT);
  _last_cycle_start = millis();
}

void SoftwarePwmActuator::update() {
  uint32_t curr_time = millis();
  if ((curr_time - _last_cmd) > _max_update_interval) {
    if (_is_active_low) {
      digitalWrite(_pin, HIGH);
    }
    else {
      digitalWrite(_pin, LOW);
    }
    return;
  }
  if (curr_time > _last_cycle_start + _period) {
    _last_cycle_start += _period;
  }
  if (curr_time < (_last_cycle_start + (_duty_cycle * _period))) {
    if (_is_active_low) {
      digitalWrite(_pin, LOW);
    }
    else {
      digitalWrite(_pin, HIGH);
    }
  }
  else {
    if (_is_active_low) {
      digitalWrite(_pin, HIGH);
    }
    else {
      digitalWrite(_pin, LOW);
    }
  }
}

void SoftwarePwmActuator::set_cmd(std_msgs::Float32 cmd) {
  _last_cmd = millis();
  float val = cmd.data;
  if (val < 0 || val > 1) {
    has_error = true;
    error_msg = "Invalid command received";
    return;
  }
  _duty_cycle = val;
}
