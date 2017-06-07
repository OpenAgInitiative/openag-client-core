#ifndef OPENAG_BINARY_ACTUATOR_H
#define OPENAG_BINARY_ACTUATOR_H

#include "Arduino.h"
#include <openag_module.h>

class BinaryActuator : public Module {
  public:
    // Constructor
    BinaryActuator(int pin, bool is_active_low, int shutoff_ms);

    // Public functions
    uint8_t begin();
    uint8_t update();
    uint8_t set_cmd(bool cmd);

  private:
    // Private variables
    int _pin;
    bool _is_active_low;
    int _shutoff_ms = 10000;
    uint32_t _last_cmd;
};

#endif
