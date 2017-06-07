#ifndef OPENAG_PULSE_ACTUATOR_H
#define OPENAG_PULSE_ACTUATOR_H

#include "Arduino.h"
#include <openag_module.h>

class PulseActuator : public Module {
  public:
    // Constructor
    PulseActuator(int pin, bool is_active_low, int pulse_ms, int update_ms);

    // Public functions
    uint8_t begin();
    uint8_t update();
    uint8_t set_cmd(bool cmd);

  private:
    uint8_t bool2command(bool isHigh);
    // Private variables
    int _pin;
    bool _is_active_low;
    bool _state; // Is ON? or OFF?
    uint32_t _pulse_ms = 50;
    int _update_ms = 4000;
    uint32_t _last_cmd;
};

#endif
