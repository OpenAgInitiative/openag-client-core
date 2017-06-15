#include "openag_air_flush.h"

AirFlush::AirFlush(int pin, bool is_active_low) {
  _pin = pin;
  _is_active_low = is_active_low;
  _cmd_start_time = 0;
  _previous_command_time = 0;
  _is_on = false;
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
}

uint8_t AirFlush::begin() {
//   Serial1.begin(9600);
//   Serial1.println("Air Flush Transmitting to Serial1");
  pinMode(_pin, OUTPUT);
  if (_is_active_low) {
    digitalWrite(_pin, HIGH);
  }
  else {
    digitalWrite(_pin, LOW);
  }
  return status_level;
}

uint8_t AirFlush::update() {
  uint32_t curr_time = millis();
  if (_is_on && ((curr_time - _cmd_start_time) > _previous_command_time)) { // turn off once exceeded on duration
    _is_on = false;
    if (_is_active_low) {
      digitalWrite(_pin, HIGH);
    }
    else {
      digitalWrite(_pin, LOW);
    }
  }
  return status_level;
}

uint8_t AirFlush::set_cmd(float cmd) {
  uint32_t cmd_ms = uint32_t(cmd * 60000); // convert minutes to milliseconds
  if ((cmd_ms != _previous_command_time) && (cmd_ms > 0)) { // only turn on if receive new command
    _is_on = true;
    _cmd_start_time = millis();
    if (_is_active_low) {
      digitalWrite(_pin, LOW);
    }
    else {
      digitalWrite(_pin, HIGH);
    }
  }
  _previous_command_time = cmd_ms;
  return status_level;
}
