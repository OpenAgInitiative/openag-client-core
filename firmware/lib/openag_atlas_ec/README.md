openag\_atlas\_ec
=================

This repository contains an OpenAg firmware module for reading from the [Atlas
Scientific EZO EC
Circuit](http://www.atlas-scientific.com/product_pages/kits/ec_k1_0_kit.html).
The module defines 1 output "water\_electrical\_conductivity" on which
electrical conductivity readings are sent at a rate of no more than 0.5 Hz. The
module will enter an ERROR state whenever it fails to read from the sensor and
will have a state of OK otherwise.

Status Codes
------------

- "31": Unknown error
- "32": No response
- "33": Request failed