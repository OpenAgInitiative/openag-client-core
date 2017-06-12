openag\_mhz16
=============

This repository contains an OpenAg firmware module for reading from the [MH-Z16
NDIR CO2 Sensor over
I2C](http://sandboxelectronics.com/?product=mh-z16-ndir-co2-sensor-with-i2cuart-5v3-3v-interface-for-arduinoraspeberry-pi).
The constructor of the module takes a single argument "i2c\_address", which is
the I2C address of the connected MHZ-16 sensor.  The module defines 1 output,
"air\_carbon\_dioxide" on which CO2 readings are sent. The module will have a
status of OK during normal operation. It will have a status of WARN while it is
being initialized and a status of ERROR if the sensor can't be read.

Status Codes
------------

- "20": Initializing
- "21": Powered off to prevent autocalibration
- "31": Failed to initialize sensor
- "32": Failed to read from sensor