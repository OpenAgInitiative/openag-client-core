# openag_mhz19
This repository contains an OpenAg firmware module for reading from the NDIR CO2 sensor based on MH-Z19 chip.
The module defines 1 output, "air_carbon_dioxide" on which reading is sent once per 5 seconds. The module will enter an ERROR state whenever it fails to read from the sensor.

Current implementation is hardcoded to read sensor values from Arduino Mega2560 Serial2 interface.

# Status Codes

- "31": CRC error

# Todo
1. Add arguments to configure interface type (Serial or PWM) and pins the sensor is attached to.

# Installation
Add to following records on your CouchDb instance:

To to firmware_module_type database:

>"{
   "_id": "mhz19",
   "description": "",
   "repository": {
       "url": "https://github.com/serein7/openag_mhz19.git",
       "type": "git"
   },
   "class_name": "Mhz19",
   "outputs": {
       "air_carbon_dioxide": {
           "type": "std_msgs/Int32"
       }
   },
   "header_file": "openag_mhz19.h",
   "dependencies": [
       {
           "url": "https://github.com/OpenAgInitiative/openag_firmware_module.git",
           "type": "git"
       }
   ]
}"

To firmware_module database: 
>"{
   "_id": "mhz19_1",
   "environment": "environment_1",
   "type": "mhz19"
}"
