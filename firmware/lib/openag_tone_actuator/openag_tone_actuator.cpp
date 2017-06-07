#include "openag_tone_actuator.h"

ToneActuator::ToneActuator(int pin, bool is_active_low, int tone_frequency, int _tone_duration) {
  _pin = pin;
  _is_active_low = is_active_low;
  _tone_frequency = tone_frequency;
  _tone_duration = _tone_duration;
  _last_cmd = 0;
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
}

uint8_t ToneActuator::begin() {
  return status_level;
}

uint8_t ToneActuator::update() {
  uint32_t curr_time = millis();
  if ((curr_time - _last_cmd) > _shutoff_ms) {
    noTone(_pin);
  }
  return status_level;
}

uint8_t ToneActuator::set_cmd(bool cmd) {
  _last_cmd = millis();
  if (cmd) {
    tone(_pin, _tone_frequency);
  }
  else {
    noTone(_pin);
  }
  return status_level;
}
