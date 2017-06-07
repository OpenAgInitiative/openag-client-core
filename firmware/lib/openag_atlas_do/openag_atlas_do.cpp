/**
 *  \file openag_atlas_do.cpp
 *  \brief Dissolved oxygen sensor.
 */
#include "openag_atlas_do.h"

AtlasDo::AtlasDo(int i2c_address) {
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  _send_water_dissolved_oxygen = false;
  _time_of_last_query = 0;
  _waiting_for_response = false;
  _i2c_address = i2c_address;
}

void AtlasDo::begin() {
  Wire.begin();
}

void AtlasDo::update() {
  if (_waiting_for_response) {
    if (millis() - _time_of_last_query > 1800) {
      read_response();
    }
  }
  else if (millis() - _time_of_last_query > _min_update_interval) {
    send_query();
  }
}

bool AtlasDo::get_water_dissolved_oxygen(std_msgs::Float32 &msg) {
  msg.data = _water_dissolved_oxygen;
  bool res = _send_water_dissolved_oxygen;
  _send_water_dissolved_oxygen = false;
  return res;
}

void AtlasDo::set_atmospheric_calibration(std_msgs::Empty msg) {
  Wire.beginTransmission(_i2c_address);
  Wire.print("Cal");
  Wire.endTransmission();
}

void AtlasDo::set_zero_calibration(std_msgs::Empty msg) {
  Wire.beginTransmission(_i2c_address);
  Wire.print("Cal,0");
  Wire.endTransmission();
}

void AtlasDo::send_query() {
  _time_of_last_query = millis();
  Wire.beginTransmission(_i2c_address); // read message response state
  Wire.print("r");
  Wire.endTransmission();
  _waiting_for_response = true;
}

void AtlasDo::read_response() {
  Wire.requestFrom(_i2c_address, 20, 1);
  byte response = Wire.read();
  String string = Wire.readStringUntil(0);

  if (response == 255) {
    status_level = ERROR;
    status_code = CODE_NO_RESPONSE;
    status_msg = "No response";
    _waiting_for_response = false;
  }
  else if (response == 254) {
    // Request hasn't been processed yet
    return;
  }
  else if (response == 2) {
    status_level = ERROR;
    status_code = CODE_REQUEST_FAILED;
    status_msg = "Request failed";
    _waiting_for_response = false;
  }
  else if (response == 1) {
    status_level = OK;
    status_code = CODE_OK;
    status_msg = "";
    _water_dissolved_oxygen = string.toFloat();
    _send_water_dissolved_oxygen = true;
    _waiting_for_response = false;
  }
  else {
    status_level = ERROR;
    status_code = CODE_UNKNOWN_ERROR;
    status_msg = "Unknown error";
    _waiting_for_response = false;
  }
}
