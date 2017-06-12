/**
 *  \file openag_atlas_orp.cpp
 *  \brief Oxidation/Reduction Potential sensor.
 */
#include "openag_atlas_orp.h"

AtlasOrp::AtlasOrp(int i2c_address) {
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  _send_water_oxidation_reduction_potential = false;
  _time_of_last_query = 0;
  _waiting_for_response = false;
  _i2c_address = i2c_address;
}

void AtlasOrp::begin() {
  Wire.begin();
}

void AtlasOrp::update() {
  if (_waiting_for_response) {
    if (millis() - _time_of_last_query > 1800) {
      read_response();
    }
  }
  else if (millis() - _time_of_last_query > _min_update_interval) {
    send_query();
  }
}

bool AtlasOrp::get_water_oxidation_reduction_potential(std_msgs::Float32 &msg) {
  msg.data = _water_oxidation_reduction_potential;
  bool res = _send_water_oxidation_reduction_potential;
  _send_water_oxidation_reduction_potential = false;
  return res;
}

void AtlasOrp::set_calibration(std_msgs::Float32 msg) {
  char buf[11];
  sprintf(buf, "Cal,%.1f", msg.data);
  Wire.beginTransmission(_i2c_address);
  Wire.print(buf);
  Wire.endTransmission();
}

void AtlasOrp::send_query() {
  _time_of_last_query = millis();
  Wire.beginTransmission(_i2c_address); // read message response state
  Wire.print("r");
  Wire.endTransmission();
  _waiting_for_response = true;
}

void AtlasOrp::read_response() {
  Wire.requestFrom(_i2c_address, 20, 1);
  byte response = Wire.read();
  String string = Wire.readStringUntil(0);

  // Check for failure
  if (response == 255) {
    status_level = ERROR;
    status_code = CODE_NO_DATA;
    status_msg = "No data";
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
  else if (response == 1) { // good reading
    status_level = OK;
    status_code = CODE_OK;
    status_msg = "";
    _water_oxidation_reduction_potential = string.toFloat();
    _send_water_oxidation_reduction_potential = true;
    _waiting_for_response = false;
  }
  else {
    status_level = ERROR;
    status_code = CODE_UNKNOWN_ERROR;
    status_msg = "Unknown error";
  }
}
