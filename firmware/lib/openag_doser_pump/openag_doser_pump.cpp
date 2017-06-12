#include "openag_doser_pump.h"

DoserPump::DoserPump(int pin, bool is_active_low) {
  _pin = pin;
  _is_active_low = is_active_low;
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
}

uint8_t DoserPump::begin() {
  pinMode(_pin, OUTPUT);
  digitalWrite(_pin, bool2command(false));
  _on_duration = 0;
  _off_duration = _dosingFreq;
  return status_level;
}

uint8_t DoserPump::update() {

  uint32_t curr_time = millis();

  // If shutoff time has passed, with no call to set_rate, set the pumps to OFF
  if(_isOn && curr_time - _last_cmd > _shutoff_ms){
    _isOn = false;
    digitalWrite(_pin, bool2command(_isOn));
    status_level = WARN;
    status_code = CODE_STALE_COMMAND;
    status_msg = "There has been no set command recently, stopping dosing.";
    return status_level;
  }

  // Dose or not dose based on the current set frequencies
  if(_isOn && curr_time - _last_pulse > _on_duration){
    _isOn = false;
    _last_pulse = curr_time;
  }
  if(!_isOn && curr_time - _last_pulse > _off_duration){
    _isOn = true;
    _last_pulse = curr_time;
  }
  digitalWrite(_pin, bool2command(_isOn));
  return status_level;
}

// Set the pump driver to pump the rate (ml/h).
uint8_t DoserPump::set_cmd(float rate) {
  uint32_t curr_time = millis();

  // TODO: Test the pumps and find their lower and upper bounds
  const float lowerBound = 100;
  const float upperBound = 1000;

  if(rate > 0 && rate < lowerBound){
    status_level = ERROR;
    status_code = CODE_LOWER_BOUND;
    status_msg = "A command to dose lower than the maximum precision was sent.";
    return status_level;
  }
  if(rate > upperBound){
    status_level = ERROR;
    status_code = CODE_UPPER_BOUND;
    status_msg = "A command to dose higher than the maximum flow rate was sent.";
    return status_level;
  }

  // TODO: test the pumps and tune the upperBound constant
  // onRatio cannot be greater than 1 if we check for upperBound above
  // Therefore we can assume that _on_duration is less than dosingFreq
  // and _off_duration is positive.
  float onRatio = rate / upperBound;

  _on_duration = (uint32_t) onRatio * _dosingFreq;
  _off_duration = (uint32_t)_dosingFreq - _on_duration;

  // Update the most recent command
  _last_cmd = curr_time;

  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  return status_level;
}

// Output a HIGH/LOW signal based on _is_active_low and the boolean passed to
// always turn on when passed true.
uint8_t DoserPump::bool2command(bool isOn){
  bool realValue = _is_active_low ? !isOn : isOn;
  return realValue ? HIGH : LOW;
}
