openag\_atlas\_do
=================

This repository contains an OpenAg firmware module for reading from the [Atlas
Scientific EZO DO
Circuit](http://www.atlas-scientific.com/product_pages/circuits/ezo_do.html).
The module defines 1 output "water\_dissolved\_oxygen" on which water DO
readings are sent at a rate of no more than 0.5 Hz. The module will enter an
ERROR state whenever it fails to read from a sensor and will have a state of OK
otherwise.

Status Codes
------------

- "31": Unknown error
- "32": No response
- "33": Request failed