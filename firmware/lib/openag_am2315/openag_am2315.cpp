/**
 *  \file openag_am2315.cpp
 *  \brief Air temperature and air humidity sensor.
 */
/***************************************************
  This is a library for the AM2315 Humidity & Temp Sensor

  Designed specifically to work with the AM2315 sensor from Adafruit
  ----> https://www.adafruit.com/products/1293

  These displays use I2C to communicate, 2 pins are required to
  interface
  Adafruit invests time and resources providing this open source code,
  please support Adafruit and open-source hardware by purchasing
  products from Adafruit!

  Written by Limor Fried/Ladyada for Adafruit Industries.
  BSD license, all text above must be included in any redistribution

  Modified for OpenAg
 ****************************************************/
#include "openag_am2315.h"

uint8_t Am2315::begin() {
  Wire.begin(); // enable i2c port
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  _time_of_last_reading = 0;
  readData();
  return status_level;
}

uint8_t Am2315::update() {
  if (millis() - _time_of_last_reading > _min_update_interval) {
      readData();
      _time_of_last_reading = millis();
  }
  return status_level;
}

float Am2315::get_air_temperature() {
    return _air_temperature;
}

float Am2315::get_air_humidity() {
    return _air_humidity;
}

bool Am2315::readData() {
  uint8_t reply[8];

  // Wake up sensor
  Wire.beginTransmission(_i2c_address);
  delay(2);
  Wire.endTransmission();

  // Send request to sensor
  Wire.beginTransmission(_i2c_address);
  Wire.write(_read_register);
  Wire.write(0x00);  // start at address 0x0
  Wire.write(4);  // request 4 bytes data
  Wire.endTransmission();

  // Give sensor time to process request
  delay(10);

  // Read sensor
  Wire.requestFrom(_i2c_address, 8);
  for (uint8_t i=0; i<8; i++) {
    reply[i] = Wire.read();
  }

  // Check for failure
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  if (reply[0] != _read_register) {
    status_level = ERROR;
    status_code = CODE_WRONG_FUNCTION_CODE;
    status_msg = String("Sensor responded with the wrong function code:") + reply[0];
    return false;
  }
  else if (reply[1] != 4) {
    status_level = ERROR;
    status_code = CODE_NOT_ENOUGH_INFO;
    status_msg = "Sensor did not return enough information";
    return false;
  }
  else { // good reading
    // Process air humidity
    _air_humidity = reply[2];
    _air_humidity *= 256;
    _air_humidity += reply[3];
    _air_humidity /= 10;

    // Process air temperature
    _air_temperature = reply[4] & 0x7F;
    _air_temperature *= 256;
    _air_temperature += reply[5];
    _air_temperature /= 10;
    if (reply[4] >> 7) _air_temperature = -_air_temperature;
  }

  if (status_level == OK) {
    return true;
  }
  return false;
}
