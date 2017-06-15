#ifndef OPENAG_PWM_ACTUATOR_H
#define OPENAG_PWM_ACTUATOR_H

#include "Arduino.h"
#include <openag_module.h>

class PwmActuator : public Module {
  public:
    // Constructor
    PwmActuator(int pin, bool is_active_low, float threshold);

    // Public functions
    uint8_t begin();
    uint8_t update();
    uint8_t set_cmd(float cmd);

  private:
    // Private variables
    int _pin;
    bool _is_active_low;
    float _threshold;
    uint32_t _last_cmd;
    const static int _max_update_interval = 10000;

    // Status codes
    static const uint8_t CODE_INVALID_COMMAND = 1;
};

#endif
