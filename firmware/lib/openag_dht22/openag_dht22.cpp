/**
 *  \file openag_dht22.cpp
 *  \brief Sensor module for air temperature and humidity.
 *  \details See openag_dht22.h for details.
 */
#include "openag_dht22.h"

Dht22::Dht22(int pin) {
  _pin = pin;
  status_level = OK;
  status_code = CODE_OK;
  status_msg = "";
}

void Dht22::begin() {
  pinMode(_pin, INPUT);
  digitalWrite(_pin, HIGH);
  _count = COUNT;
  _first_reading = true;
  _time_of_last_reading = 0;
}

void Dht22::update() {
  if (millis() - _time_of_last_reading > _min_update_interval) {
    getData();
    _time_of_last_reading = millis();
  }
}

bool Dht22::get_air_temperature(std_msgs::Float32 &msg) {
  msg.data = _air_temperature;
  bool res = _send_air_temperature;
  _send_air_temperature = false;
  return res;
}

bool Dht22::get_air_humidity(std_msgs::Float32 &msg) {
  msg.data = _air_humidity;
  bool res = _send_air_humidity;
  _send_air_humidity = false;
  return res;
}

void Dht22::getData(void) {
  if (readSensor()) {
    if (status_level != OK) {
      status_level = OK;
      status_code = CODE_OK;
      status_msg = "";
    }

    _air_humidity = _data[0];
    _air_humidity *= 256;
    _air_humidity += _data[1];
    _air_humidity /= 10;

    _air_temperature = _data[2] & 0x7F;
    _air_temperature *= 256;
    _air_temperature += _data[3];
    _air_temperature /= 10;
    if (_data[2] & 0x80) {
      _air_temperature *= -1;
    }
    _send_air_temperature = true;
    _send_air_humidity = true;
  }
  else {
    status_level = ERROR;
    status_code = CODE_FAILED_TO_READ;
    status_msg = "Failed to read from sensor";
  }
}

bool Dht22::readSensor() {
  uint8_t last_state = HIGH;
  uint8_t counter = 0;
  uint8_t j = 0, i;
  unsigned long current_time;

  digitalWrite(_pin, HIGH);
  delay(2); // old delay time was 250

  current_time = millis();
  if (current_time < _last_read_time) {
    // ie there was a rollover
    _last_read_time = 0;
  }
  if (!_first_reading && ((current_time - _last_read_time) < 2000)) {
    return true; // return last correct measurement
  }
  _first_reading = false;
  _last_read_time = millis();

  _data[0] = _data[1] = _data[2] = _data[3] = _data[4] = 0;

  // now pull it low for ~20 milliseconds
  pinMode(_pin, OUTPUT);
  digitalWrite(_pin, LOW);
  delay(20);
  digitalWrite(_pin, HIGH);
  delayMicroseconds(40);
  pinMode(_pin, INPUT);

  // read in timings
  for ( i=0; i< MAXTIMINGS; i++) {
    counter = 0;
    while (digitalRead(_pin) == last_state) {
      counter++;
      delayMicroseconds(1);
      if (counter == 255) {
        break;
      }
    }
    last_state = digitalRead(_pin);

    if (counter == 255) break;

    // ignore first 3 transitions
    if ((i >= 4) && (i%2 == 0)) {
      // shove each bit into the storage bytes
      _data[j/8] <<= 1;
      if (counter > _count)
        _data[j/8] |= 1;
      j++;
    }
  }

  // check we read 40 bits and that the checksum matches
  if ((j >= 40) &&
      (_data[4] == ((_data[0] + _data[1] + _data[2] + _data[3]) & 0xFF)) ) {
    return true;
  }
  return false;
}
