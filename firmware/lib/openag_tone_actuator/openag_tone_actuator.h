#ifndef OPENAG_TONE_ACTUATOR_H
#define OPENAG_TONE_ACTUATOR_H

#include "Arduino.h"
#include <openag_module.h>

class ToneActuator : public Module {
  public:
    // Constructor
    ToneActuator(int pin, bool is_active_low, int tone_frequency, int tone_duration);

    // Public functions
    uint8_t begin();
    uint8_t update();
    uint8_t set_cmd(bool cmd);

  private:
    // Private variables
    int _pin;
    bool _is_active_low;
    int _tone_frequency = 140;
    int _tone_duration = -1;
    uint32_t _shutoff_ms = 10000;
    uint32_t _last_cmd;
};

#endif
