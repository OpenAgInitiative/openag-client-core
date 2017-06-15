/**
 *  \file openag_bh1750.cpp
 *  \brief Light intensity sensor based on BH1750 chip.
 */
/***************************************************
  Based on sample code from http://blog.simtronyx.de/en/measurement-of-illuminance-with-a-bh1750fvi-breakout-board-gy-30-and-an-arduino-uno/

  Modified for OpenAg
 ****************************************************/
#include "openag_bh1750.h"

void Bh1750::begin() {
  Wire.begin(); // enable i2c port
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  _send_light_illuminance = false;
  _time_of_last_reading = 0;
}

void Bh1750::update() {
  if (millis() - _time_of_last_reading > _min_update_interval) {
      readData();
      _time_of_last_reading = millis();
  }
}

bool Bh1750::get_light_illuminance(std_msgs::UInt16 &msg) {
  msg.data = _light_illuminance;
  bool res = _send_light_illuminance;
  _send_light_illuminance = false;
  return res;
}


void Bh1750::readData() {
  uint8_t reply[4];

  // Wake up sensor
  Wire.beginTransmission(_i2c_address);
  Wire.write(0x10); // 1 lux resolution
  Wire.endTransmission();
  delay(200);
  // Send request to sensor
  byte i=0;
  Wire.beginTransmission(_i2c_address);
  Wire.requestFrom(_i2c_address, 2);
  while(Wire.available() && i<4){
    reply[i] = Wire.read();
    i++;
  }
  Wire.endTransmission();
  _light_illuminance = (uint16_t)(((reply[0]<<8)|reply[1])/1.2);
  if(i==2 && _light_illuminance>0) {
      _send_light_illuminance = true;
      status_level = OK;
      status_code = CODE_OK;
      status_msg = "";
  } else {
    status_level = ERROR;
    status_code = CODE_INVALID_SENSOR_RESPONSE;
    status_msg = "Sensor response is invalid";
  }
}
