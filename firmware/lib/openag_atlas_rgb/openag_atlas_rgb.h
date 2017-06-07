/**
 *  \file openag_atlas_rgb.h
 *  \brief Illuminance and light spectrum rgb sensor.
 */
#ifndef OPENAG_ATLAS_RGB
#define OPENAG_ATLAS_RGB

#if (ARDUINO >= 100)
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

#include <openag_module.h>
#include <std_msgs/UInt16.h>
#include <std_msgs/UInt8MultiArray.h>

/**
 * \brief Illuminance, light spectrum rgb sensor.
 */
class AtlasRgb : public Module {
  public:
    // Constructor
    AtlasRgb(int serial_port);

    // Public functions
    void begin();
    void update();
    bool get_light_illuminance(std_msgs::UInt16 &msg);
    bool get_light_spectrum(std_msgs::UInt8MultiArray &msg);

  private:
    // Private variables
    uint16_t _light_illuminance;
    uint8_t _light_spectrum[3];
    bool _send_light_illuminance;
    bool _send_light_spectrum;
    uint32_t _time_of_last_reading;
    const static uint32_t _min_update_interval = 2000;
    HardwareSerial* _serial_port;

    // Private functions
    void readData();

    // Status codes
    static const uint8_t CODE_FAILED_TO_READ = 1;
    static const uint8_t CODE_INVALID_RESPONSE = 2;
};

#endif
