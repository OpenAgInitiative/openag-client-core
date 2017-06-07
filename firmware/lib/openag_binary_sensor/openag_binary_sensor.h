#ifndef OPENAG_BINARY_SENSOR_H
#define OPENAG_BINARY_SENSOR_H

#include "Arduino.h"
#include <openag_module.h>

class BinarySensor : public Module {
  public:
    // Constructor
    BinarySensor(int pin, bool is_active_low);

    // Methods
    uint8_t begin();
    uint8_t update();
    bool get_is_on();

  private:
    // Private variables
    float _is_on;
    int _pin;
    bool _is_active_low;
    uint32_t _time_of_last_reading;
    const static uint32_t _min_update_interval = 2000;

    // Private methods
    void readData();
};

#endif
