/**
 *  \file openag_gc0012.h
 *  \brief Carbon Dioxide Sensor
 */
#ifndef OPENAG_GC0012_H
#define OPENAG_GC0012_h

#include "Arduino.h"
#include <openag_module.h>
#include <std_msgs/Float32.h>

/**
 * \brief Carbon dioxide sensor
 */
class Gc0012 : public Module {
  public:
    Gc0012(int serial_port);

    // Public functions
    void begin();
    void update();
    bool get_air_carbon_dioxide(std_msgs::Float32 &msg);

  private:
    // Private variables
    float _carbon_dioxide;
    bool _send_carbon_dioxide;
    uint32_t _time_of_last_reading;
    const static uint32_t _min_update_interval = 2000;
    HardwareSerial *_serial_port;

    // Private functions
    void readData();

    // Status codes
    static const uint8_t CODE_FAILED_TO_READ = 2;
};

#endif
