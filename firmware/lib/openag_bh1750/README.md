openag\_bh1750
=============

This repository contains an OpenAg firmware module for reading from the
Digital Light Intensity Sensor based on BH1750 chip. The module defines 1 output,
"light\_intensity" on which reading is sent at a rate of no more than 0.5 Hz. The module
will enter an ERROR state whenever it fails to read from the sensor.

Status Codes
------------

- "31": Sensor response is invalid