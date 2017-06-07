openag\_am2315
=============

[![Build Status](https://travis-ci.org/OpenAgInitiative/openag_am2315.svg?branch=master)](https://travis-ci.org/OpenAgInitiative/openag_am2315)

This repository contains an OpenAg firmware module for reading from the
[Adafruit Am2315 I2C Temperature/Humidity
Sensor](https://www.adafruit.com/product/1293). The module defines 2 outputs,
"air\_temperature" and "air\_humidity" on which temperature and humidity
readings, respectively, are sent at a rate of no more than 0.5 Hz. The module
will enter an ERROR state whenever it fails to read from the sensor.

Status Codes
------------

- "32": Sensor responded with the wrong function code
- "33": Sensor did not return enough information
