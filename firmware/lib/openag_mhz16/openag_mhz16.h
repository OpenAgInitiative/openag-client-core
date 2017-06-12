#ifndef OPENAG_MHZ16
#define OPENAG_MHZ16

#include "Arduino.h"
#include <Wire.h>
#include "NDIR_I2C.h"
#include <openag_module.h>


class MHZ16 : public Module {
  public:
    MHZ16(int i2c_address);
    uint8_t begin();
    uint8_t update();
    int get_air_carbon_dioxide();

  private:
    NDIR_I2C _sensor;
    bool _send_air_carbon_dioxide;
    uint32_t _init_time;
    bool _initializing;
    uint32_t _time_of_last_reading;
    const static uint32_t _min_update_interval = 2000;
    bool _is_on;
    const static uint32_t _leave_off_for = 2000;
    uint32_t _time_of_last_power_cycle;
    const static uint32_t _power_cycle_interval = 43200000;

    void readData();

    // Status codes
    static const uint8_t CODE_INITIALIZING = 1;
    static const uint8_t CODE_INTENTIONAL_POWER_OFF = 2;
    static const uint8_t CODE_FAILED_TO_INITIALIZE = 3;
    static const uint8_t CODE_FAILED_TO_READ = 4;

};

#endif
