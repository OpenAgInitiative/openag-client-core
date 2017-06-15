/**
 *  \file openag_atlas_ec.cpp
 *  \brief Electrical conductivity sensor.
 */
#include "openag_atlas_ec.h"

AtlasEc::AtlasEc(int i2c_address) {
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  _time_of_last_query = 0;
  _waiting_for_response = false;
  _i2c_address = i2c_address;
}

uint8_t AtlasEc::begin() {
  Wire.begin();
  Wire.setTimeout(40);
  // Enable only the EC reading
  Wire.print("O,EC,1");
  Wire.print("O,TDS,0");
  Wire.print("O,S,0");
  Wire.print("O,SG,0");
  return status_level;
}

uint8_t AtlasEc::update() {
  if (_waiting_for_response) {
    if (millis() - _time_of_last_query > 1400) {
      read_response();
    }
  }
  else if (millis() - _time_of_last_query > _min_update_interval) {
    send_query();
  }
  return status_level;
}

float AtlasEc::get_water_electrical_conductivity() {
  return _water_electrical_conductivity;
}

void AtlasEc::set_dry_calibration() {
  Wire.beginTransmission(_i2c_address);
  Wire.print("Cal,dry");
  Wire.endTransmission();
}

void AtlasEc::set_single_calibration(double msg) {
  char buf[17];
  sprintf(buf, "Cal,one,%.2f", msg);
  Wire.beginTransmission(_i2c_address);
  Wire.print(buf);
  Wire.endTransmission();
}

void AtlasEc::set_lowpoint_calibration(double msg) {
  char buf[17];
  sprintf(buf, "Cal,low,%.2f", msg);
  Wire.beginTransmission(_i2c_address);
  Wire.print(buf);
  Wire.endTransmission();
}

void AtlasEc::set_highpoint_calibration(double msg) {
  char buf[17];
  sprintf(buf, "Cal,high,%.2f", msg);
  Wire.beginTransmission(_i2c_address);
  Wire.print(buf);
  Wire.endTransmission();
}

void AtlasEc::send_query() {
  _time_of_last_query = millis();
  Wire.beginTransmission(_i2c_address); // read message response state
  Wire.print("r");
  Wire.endTransmission();
  _waiting_for_response = true;
}

void AtlasEc::read_response() {
  Wire.requestFrom(_i2c_address, 20, 1);
  byte response;
  String string = "1000";
  if(Wire.available()){
    response = Wire.read();
  }

  // Check for failure
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
    string = Wire.readStringUntil(0);
    status_level = OK;
    status_code = CODE_OK;
    status_msg = "";
    _water_electrical_conductivity = string.toFloat() / 1000;
    _waiting_for_response = false;
  }
  else {
    status_level = ERROR;
    status_code = CODE_UNKNOWN_ERROR;
    status_msg = "Unknown error";
  }
}
