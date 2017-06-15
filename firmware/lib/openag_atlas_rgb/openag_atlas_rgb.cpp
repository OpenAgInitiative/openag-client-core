/**
 *  \file openag_atlas_rgb.cpp
 *  \brief Illuminance and light spectrum rgb sensor.
 */

 #include "openag_atlas_rgb.h"

AtlasRgb::AtlasRgb(int serial_port) {
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
  _send_light_illuminance = false;
  _send_light_spectrum = false;
  _time_of_last_reading = 0;
  switch(serial_port) {
    case 1:
      _serial_port = &Serial1;
      break;
    case 2:
      _serial_port = &Serial2;
      break;
    case 3:
      _serial_port = &Serial3;
      break;
  }
}

void AtlasRgb::begin(void) {
  // Enable serial port
  _serial_port->begin(9600);

  // Set operation modes
  _serial_port->print("RESPONSE,0\r"); // disable response code
  _serial_port->print("C,0\r"); // disable streaming
  _serial_port->print("O,RGB,1\r"); // enable rgb readings
  _serial_port->print("O,PROX,0\r"); // disable proximity readings
  _serial_port->print("O,LUX,1\r"); // enable lux readings
  _serial_port->print("O,CIE,0\r"); // disable cie readings
  _serial_port->print("RESPONSE,1\r"); // enable response code
  _serial_port->readStringUntil(13);
}

  // Check For Failure
  // _serial_port->print("RESPONSE,1\r"); // enable response code
  // String string = Serial3.readStringUntil(13);
  // String ok_string = "*OK";
  // if (!string.equals(ok_string)) { // check sensor responds *OK
  //   _sensor_failure = true;
  // }
  // else {
  // }

  // String(id + ":" + String(red) + "," + String(green) + "," + String(blue));

void AtlasRgb::update() {
  if (millis() - _time_of_last_reading > _min_update_interval) {
    readData();
    _time_of_last_reading = millis();
  }
}

bool AtlasRgb::get_light_illuminance(std_msgs::UInt16 &msg) {
  msg.data = _light_illuminance;
  bool res = _send_light_illuminance;
  _send_light_illuminance = false;
  return res;
}

bool AtlasRgb::get_light_spectrum(std_msgs::UInt8MultiArray &msg) {
  msg.data_length = 3;
  msg.data = _light_spectrum;
  bool res = _send_light_spectrum;
  _send_light_spectrum = false;
  return res;
}

void AtlasRgb::readData() {
  // Read sensor
  _serial_port->print("R\r");
  String response = _serial_port->readStringUntil(13);
  String data_string = _serial_port->readStringUntil(13);

  // Check for failure
  String ok_string = "*OK";
  if (!response.equals(ok_string)) {
    status_level = ERROR;
    status_code = CODE_FAILED_TO_READ;
    status_msg = "Failed to read data";
  }
  else {
    _send_light_illuminance = true;
    _send_light_spectrum = true;

    // RGB values over 255 indicate that recalibration is required. We can't
    // detect these using 8-bit integers, so we use a 16-bit integer buffer
    // when parsing the response string.
    uint16_t buff;

    // Process red value
    int start_index = 0;
    int end_index = data_string.indexOf(',');
    buff = data_string.substring(start_index, end_index).toInt();
    _light_spectrum[0] = buff;
    if (buff != _light_spectrum[0]) {
      _send_light_spectrum = false;
      status_level = ERROR;
      status_code = CODE_INVALID_RESPONSE;
      status_msg = "Invalid response. Recalibration required.";
    }

    // Process green value
    start_index = end_index + 1;
    end_index = data_string.indexOf(',', start_index);
    buff = data_string.substring(start_index, end_index).toInt();
    _light_spectrum[1] = buff;
    if (buff != _light_spectrum[1]) {
      _send_light_spectrum = false;
      status_level = ERROR;
      status_code = CODE_INVALID_RESPONSE;
      status_msg = "Invalid response. Recalibration required.";
    }

    // Process blue value
    start_index = end_index + 1;
    end_index = data_string.indexOf(',', start_index);
    buff = data_string.substring(start_index, end_index).toInt();
    _light_spectrum[2] = buff;
    if (buff != _light_spectrum[2]) {
      _send_light_spectrum = false;
      status_level = ERROR;
      status_code = CODE_INVALID_RESPONSE;
      status_msg = "Invalid response. Recalibration required.";
    }

    // Process illuminance value
    start_index = end_index + 1; // skip over "Lux"
    end_index = data_string.indexOf(',', start_index);
    start_index = end_index + 1;
    end_index = data_string.indexOf(',', start_index);
    _light_illuminance = data_string.substring(start_index, end_index).toInt();
  }
}
