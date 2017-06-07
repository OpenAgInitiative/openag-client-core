/**
 *  \file dht22.h
 *  \brief Sensor module for air temperature and humidity.
 */

#ifndef OPENAG_DHT22_H
#define OPENAG_DHT22_H

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

// 8 MHz(ish) AVR ---------------------------------------------------------
#if (F_CPU >= 7400000UL) && (F_CPU <= 9500000UL)
#define COUNT 3
// 16 MHz(ish) AVR --------------------------------------------------------
#elif (F_CPU >= 15400000UL) && (F_CPU <= 19000000L)
#define COUNT 6
#else
#error "CPU SPEED NOT SUPPORTED"
#endif

// how many timing transitions we need to keep track of. 2 * number bits + extra
#define MAXTIMINGS 85

#include <openag_module.h>
#include <std_msgs/Float32.h>

/**
 *  \brief Sensor module for air temperature and humidity.
 */
class Dht22 : public Module {
  public:
    // Public Functions
    Dht22(int pin);
    void begin();
    void update();
    bool get_air_temperature(std_msgs::Float32 &msg);
    bool get_air_humidity(std_msgs::Float32 &msg);

  private:
    // Private Functions
    void getData();
    bool readSensor();

    // Private Variables
    int _pin;
    float _air_temperature;
    bool _send_air_temperature;
    float _air_humidity;
    bool _send_air_humidity;
    uint32_t _time_of_last_reading;
    const uint32_t _min_update_interval = 2000;

    uint8_t _data[6];
    uint8_t _count;
    uint32_t _last_read_time;
    bool _first_reading;

    // Status codes
    static const uint8_t CODE_FAILED_TO_READ = 1;
};

#endif

