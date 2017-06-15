#ifndef OPENAG_AIR_FLUSH_H
#define OPENAG_AIR_FLUSH_H

#include "Arduino.h"
#include <openag_module.h>

class AirFlush : public Module {
  public:
    // Constructor
    AirFlush(int pin, bool is_active_low);

    // Public functions
    uint8_t begin();
    uint8_t update();
    uint8_t set_cmd(float cmd);

  private:
    // Private variables
    int _pin;
    uint32_t _cmd_start_time;
    bool _is_active_low;
    bool _is_on;
    uint32_t _previous_command_time;
};

#endif
