/**
 *  \file openag_bh1750.h
 *  \brief Light intensity sensor based on BH1750 chip.
 */
/***************************************************
  Based on sample code from http://blog.simtronyx.de/en/measurement-of-illuminance-with-a-bh1750fvi-breakout-board-gy-30-and-an-arduino-uno/

  Modified for OpenAg
 ****************************************************/
#ifndef OPENAG_BH1750
#define OPENAG_BH1750

#if defined(ARDUINO) && (ARDUINO >= 100)
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

#if defined(__AVR__)
  #include <util/delay.h>
#endif

#include <Wire.h>
#include <openag_module.h>
#include <std_msgs/UInt16.h>

/**
 * \brief Air temperature and air humidity sensor.
 */
class Bh1750 : public Module {

  public:
    void begin();
    void update();
    bool get_light_illuminance(std_msgs::UInt16 &msg);

  private:
    // Private variables
    uint16_t _light_illuminance;
    bool _send_light_illuminance;
    uint32_t _time_of_last_reading;
    const static uint32_t _min_update_interval = 2000;
    const static int _i2c_address = 0x23;
    const static int _read_register = 0x03;

    // Private methods
    void readData();

    // Status codes
    static const uint8_t CODE_INVALID_SENSOR_RESPONSE = 31;
};

#endif
