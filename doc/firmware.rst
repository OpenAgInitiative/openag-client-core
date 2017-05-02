.. _Firmware:

Firmware
========

The firmware system takes care of generating sensor and actuator firmware code for the Arduino, as well as building ``.hex`` files and flashing the Arduino.

The firmware system is made up of many small C++ modules, each handling the glue to talk to a single actuator or sensor. These modules are stitched together into an Arduino sketch by a small codegen system, and the resulting sketch is compiled into a ``.hex`` file.

Where Things Are
----------------

- The firmware build script can be found at `scripts/firmware`.
- The source code for individual firmware modules can be found in ``firmware/lib``. These module files are compiled into an Arduino sketch by the codegen system.
- The generated sketch is placed in ``firmware/src/src.ino``.
- The compiled ``.hex`` file is placed in
  ``firmware/.pioenvs/megaatmega2560/firmware.hex``. This is the default
  location in which platformio places hex files.

Configuring Firmware
--------------------

You can configure firmware for the Arduino with a ``.yaml`` file.

By convention, we use the same ``.yaml`` manifest file to:

1. Describe the firmware configuration that should be generated and flashed to the Arduino.
2. Load that same configuration as a set of params for openag_brain. This lets openag_brain know what information will be coming from the Arduino. See :ref:`ROSNodes` for more on ``.launch`` files and params.

See ``launch/personal_food_computer_v2.yaml`` for an example of a firmware configuration file.

Building Firmware
-----------------

The `install_dev` script installs [platformio](http://docs.platformio.org/en/latest/ide/atom.html), a tool for building Arduino binaries. However, before you can use the firmware build system, you need to initialize platformio **just once** from the directory you plan run the flash script in.

    rosrun openag_brain init_pio

This will create config files and a build space for platformio.

Now, firmware can be built with the `scripts/firmware` utility.

Get info on how to use it::

    rosrun openag_brain firmware -h

Build firmware for personal food computer::

    rosrun openag_brain firmware launch/personal_food_computer_v2.yaml

Build firmware and flash to Arduino::

    rosrun openag_brain firmware --target upload launch/personal_food_computer_v2.yaml

Authoring Firmware Modules
--------------------------

Firmware modules are C++ classes handle reading from sensors or posting to actuators on the Arduino.

Firmware modules must follow a specific format so that this project can automatically generate Arduino code. The classes must define the following properties and functions:

.. cpp:member:: bool has_error

  This attribute should be set to True to indicate that the firmware module
  encountered an error in operation.

.. cpp:member:: char* error_msg

  This attribute should hold a string describing the error that occurred
  whenever `has_error` is true.

.. cpp:function:: void begin()

  This function can be used to initialize the module and its attributes.

.. cpp:function:: void update()

  This function is called once per loop and should do the bulk of the work for
  the module. For example, if the module is a driver for a sensor, this
  function should read from the sensor and store the read data somewhere
  internally.

.. cpp:function:: bool get_<variable>(<msg_type> &msg)

  The module must define a getter in this format for every variable it outputs.
  For example, if a module outputs air_temperature as a 32-bit floating point
  number, it should define a function `get_air_temperature(std_msgs::Float32
  &msg)`. The function should populate the message object that is passed in
  with the value read from the sensor and return a boolean value indicating
  whether or not the message should be sent out to the Raspberry Pi.

Release Management
------------------

For each tagged release of openag_brain software, we should build a corresponding firmware ``.hex`` file and upload it to the release.

Users can use this ``.hex`` file to flash their Arduino with a known good configuration.