/**
 *  \file openag_atlas_do.h
 *  \brief Dissolved oxygen sensor.
 */
#ifndef OPENAG_ATLAS_DO_H
#define OPENAG_ATLAS_DO_H

#include "Arduino.h"
#include "openag_module.h"
#include <Wire.h>
#include <std_msgs/Float32.h>
#include <std_msgs/Empty.h>

/**
 * \brief Dissolved oxygen sensor.
 */
class AtlasDo : public Module {
  public:
    // Constructor
    AtlasDo(int i2c_address); // Default is 97

    // Public functions
    void begin();
    void update();
    bool get_water_dissolved_oxygen(std_msgs::Float32 &msg);
    void set_atmospheric_calibration(std_msgs::Empty msg);
    void set_zero_calibration(std_msgs::Empty msg);

  private:
    // Private variables
    float _water_dissolved_oxygen;
    bool _send_water_dissolved_oxygen;
    uint32_t _time_of_last_query;
    bool _waiting_for_response;
    const static uint32_t _min_update_interval = 3000;
    int _i2c_address;

    // Private functions
    void send_query();
    void read_response();

    // Status codes
    static const uint8_t CODE_NO_RESPONSE = 1;
    static const uint8_t CODE_REQUEST_FAILED = 2;
    static const uint8_t CODE_UNKNOWN_ERROR = 3;
};

 #endif
