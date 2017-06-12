/**
 *  \file openag_atlas_orp.h
 *  \brief Oxidation/Reduction Potential sensor.
 */
#ifndef OPENAG_ATLAS_ORP_H
#define OPENAG_ATLAS_ORP_H

#include "Arduino.h"
#include <Wire.h>
#include <openag_module.h>
#include <std_msgs/Float32.h>

/**
 * \brief Oxidation/Reduction Potential sensor.
 */
class AtlasOrp : public Module {
  public:
    // Constructor
    AtlasOrp(int i2c_address); // Default is 98

    // Public functions
    void begin();
    void update();
    bool get_water_oxidation_reduction_potential(std_msgs::Float32 &msg);
    void set_calibration(std_msgs::Float32 msg);

  private:
    // Private variables
    float _water_oxidation_reduction_potential;
    bool _send_water_oxidation_reduction_potential;
    uint32_t _time_of_last_query;
    bool _waiting_for_response;
    const static uint32_t _min_update_interval = 3000;
    int _i2c_address;

    // Private functions
    void send_query();
    void read_response();

    // Status codes
    static const uint8_t CODE_NO_DATA = 1;
    static const uint8_t CODE_REQUEST_FAILED = 2;
    static const uint8_t CODE_UNKNOWN_ERROR = 3;
};

 #endif
