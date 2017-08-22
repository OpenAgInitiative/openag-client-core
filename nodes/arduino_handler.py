#!/usr/bin/python
"""
This ROS node Handles Arduino messages and publishes them to ROS topics
It also receives env_var/commanded topics and sends messages to the Arduino accordingly.


Usage (in ROS launchfile):
<node pkg="openag_brain" type="arduino_handler.py" name="arduino_handler">
  <param name="serial_port_id" value="/dev/ttyACM0" type="str"/>
  <param name="publisher_rate_hz" value="1" type="int"/>
  <param name="serial_rate_hz" value="1" type="int"/>
  <param name="baud_rate" value="115200" type="int"/>
</node>
"""
import serial
import rospy
import os
from collections import OrderedDict
from std_msgs.msg import String
from roslib.message import get_message_class
from openag_brain.load_env_var_types import VariableInfo
from openag_brain.settings import trace, TRACE

# below: immutables/consts
# csv_headers will be hard coded since it will be tightly coupled with Arduino sketch anyways.
# the associated types are also included in the tuple since it is usually relevant to have around.
sensor_csv_headers = OrderedDict([
    ("status", int),
    ("air_humidity", float),
    ("air_temperature", float),
    ("air_carbon_dioxide", float),
    ("water_temperature", float),
    ("water_level_low", float),
    ("water_level_high", float),
    ("water_potential_hydrogen", float),
    ("water_electrical_conductivity", float)
])

actuator_csv_headers =  OrderedDict([
    ("status", int),
    ("pump_1_nutrient_a_1", float),
    ("pump_2_nutrient_b_1", float),
    ("pump_3_ph_up_1", bool),
    ("pump_4_ph_down_1", bool),
    ("pump_5_water_1", bool),
    ("chiller_fan_1", bool),
    ("chiller_pump_1", bool),
    ("heater_core_2_1", bool),
    ("air_flush_1", float),
    ("water_aeration_pump_1", bool),
    ("water_circulation_pump_1", bool),
    ("chamber_fan_1", bool),
    ("light_intensity_blue", float),
    ("light_intensity_white", float),
    ("light_intensity_red", float),
    ("heater_core_1_1", bool),
    ("chiller_compressor_1", bool)
])

actuator_listen_variables = (
    "air_temperature",
    "water_potential_hydrogen",
    "nutrient_flora_duo_a",
    "nutrient_flora_duo_b",
    "air_flush",
    "light_intensity_red",
    "light_intensity_blue",
    "light_intensity_white",
    "water_level_high"
)

# Store latest actuator and sensor states we are aware of.
actuator_state = {
    header: actuator_csv_headers[header]()
    for header in actuator_csv_headers
}
sensor_state = {}

# Declare this global so our code can be tested!
serial_connection = None

ENVIRONMENTAL_VARIABLES = frozenset(
    VariableInfo.from_dict(d)
    for d in rospy.get_param("/var_types/environment_variables").itervalues())

VALID_SENSOR_VARIABLES = [v for v in ENVIRONMENTAL_VARIABLES
    if v.name in sensor_csv_headers]

PUBLISHERS = {
    variable.name: rospy.Publisher(
        "{}/raw".format(variable.name),
        get_message_class(variable.type),
        queue_size=10)
    for variable in VALID_SENSOR_VARIABLES
}

ARDUINO_STATUS_PUBLISHER = rospy.Publisher(
    "/arduino_status",
    String,
    queue_size=10)

VALID_ACTUATOR_VARIABLES = [v for v in ENVIRONMENTAL_VARIABLES
    if v.name in actuator_listen_variables]

STATUS_CODE_INDEX = {
    "0": {
        "is_ok": True,
        "message": "OK"
    },
    "1": {
        "is_ok": False,
        "message": "WARN"
    },
    "2": {
        "is_ok": False,
        "message": "ERROR"
    }
}

def recipe_end_callback(msg):

    for header in actuator_state:
        actuator_state[header] = actuator_csv_headers[header]()

# These are callbacks that map the */commanded topic to the Arduino actuators.
# This is a job that was traditionally done by topic_connector.py, but
# these are hardcoded configurations even though the configuration is in the
# personal_food_computer_v2.yaml file because we removed the codegen from
# `firmware`, and you would need to rewrite both this node and the config file
# if you changed the topic mapping.
# This direct mapping will also let the future `actuator_node`
# for single actuators to listen in on */commanded topics and decide to actuate
# based on the information individually instead of having to write a config.
# 6/7/2017 Rikuo Hasegawa(Spaghet)
def air_temperature_callback(msg): # float -1~1
    command = msg.data
    up = (
        ("heater_core_2_1", actuator_csv_headers["heater_core_2_1"]),
        ("heater_core_1_1", actuator_csv_headers["heater_core_1_1"])
    )
    down = (
        ("chiller_fan_1", actuator_csv_headers["chiller_fan_1"]),
        ("chiller_pump_1", actuator_csv_headers["chiller_pump_1"]),
        ("chiller_compressor_1", actuator_csv_headers["chiller_compressor_1"])
    )
    always = (
        ("chamber_fan_1", actuator_csv_headers["chamber_fan_1"]),
    )
    # Reset the state to idle
    for header, type_constructor in up + down:
        actuator_state[header] = type_constructor(False)
    for header, type_constructor in always:
        actuator_state[header] = type_constructor(True)

    # Set actuator_state based on command
    if (command > 0):
        for header, type_constructor in up:
            actuator_state[header] = type_constructor(True)
    if (command < 0):
        for header, type_constructor in down:
            actuator_state[header] = type_constructor(True)


def water_potential_hydrogen_callback(msg): # float -1 ~ 1
    command = msg.data

    # reset state to idle
    actuator_state["pump_3_ph_up_1"] = False
    actuator_state["pump_4_ph_down_1"] = False

    # Set actuator_state based on command
    if command > 0:
        actuator_state["pump_3_ph_up_1"] = True
    elif command < 0:
        actuator_state["pump_4_ph_down_1"] = True


# nutrient_flora_duo_a is a "Rate" of dosage, so we can just change the dosage
# without resetting to "idle state" since that doesn't exist.
def nutrient_flora_duo_a_callback(msg): # float
    command = actuator_csv_headers["pump_1_nutrient_a_1"](msg.data)
    actuator_state["pump_1_nutrient_a_1"] = command


def nutrient_flora_duo_b_callback(msg): # float
    command = actuator_csv_headers["pump_2_nutrient_b_1"](msg.data)
    actuator_state["pump_2_nutrient_b_1"] = command


def air_flush_callback(msg): # float 0/1
    command = actuator_csv_headers["air_flush_1"](msg.data)
    actuator_state["air_flush_1"] = float(command)


def light_intensity_blue_callback(msg): # float 0~1
    command = actuator_csv_headers["light_intensity_blue"](msg.data)
    actuator_state["light_intensity_blue"] = command


def light_intensity_white_callback(msg): # float 0~1
    command = actuator_csv_headers["light_intensity_white"](msg.data)
    actuator_state["light_intensity_white"] = command


def light_intensity_red_callback(msg): # float 0~1
    command = actuator_csv_headers["light_intensity_red"](msg.data)
    actuator_state["light_intensity_red"] = command


# The water level sensor is HIGH when dry, which gets passed through the
# linear_controller node, which takes the sensor value */measured (EWMA)
# and passes it as */commanded. We should set the pump_5_water_1 to HIGH when
# we receive a value larger than 0.5 here. The values are usually close to 0 or 1.
# TODO: I want to deprecate this with something more feedback loop oriented:
# See https://github.com/OpenAgInitiative/openag_brain/issues/270 for details
def water_level_high_callback(msg): # float 1 / 0
    command = msg.data
    # if the high water level is >= .5, turn the pump on
    actuator_state["pump_5_water_1"] = command >= 0.5


CALLBACKS = {
    "air_temperature":          air_temperature_callback,
    "water_potential_hydrogen": water_potential_hydrogen_callback,
    "nutrient_flora_duo_a":     nutrient_flora_duo_a_callback,
    "nutrient_flora_duo_b":     nutrient_flora_duo_b_callback,
    "air_flush":                air_flush_callback,
    "light_intensity_red":      light_intensity_red_callback,
    "light_intensity_blue":     light_intensity_blue_callback,
    "light_intensity_white":    light_intensity_white_callback,
    "water_level_high":         water_level_high_callback
}

SUBSCRIBERS = {
    variable.name: rospy.Subscriber(
        "{}/commanded".format(variable.name),
        get_message_class(variable.type),
        CALLBACKS[variable.name]
        )
    for variable in VALID_ACTUATOR_VARIABLES
}
recipe_end_subscriber = rospy.Subscriber(
    "{ns}recipe_end/desired".format(ns=rospy.get_namespace()),
    String,
    recipe_end_callback
)

def expand_unknown_status(status_code):
    return {
        "is_ok": False,
        "message": "Unknown status code {}".format(status_code)
    }

# Closures are passed by reference such that any new substitutions are interpreted
# as declarations, causing prev_time to be "Referenced before declaration".
# This can be bypassed using an object reference
# https://stackoverflow.com/questions/3190706/nonlocal-keyword-in-python-2-x
def ros_next(rate_hz):
    ros_next.prev_time = rospy.get_time()
    timeout = 1 / rate_hz
    def closure():
        curr_time = rospy.get_time()
        if curr_time - ros_next.prev_time > timeout:
            ros_next.prev_time = curr_time
            return True
        else:
            return False
    return closure

# Read and verify the serial message string.
def process_message(line):
    trace('arduino_handler serial read: >%s<', line.replace('\n',''))
    # detect an empty and a line with only a \n char:
    if len(line) <= 1:
        return "No message"
    try:
        values = line[:-1].decode().split(',')
        status_code = values[0]
        # Expand status code to status dict
        status = (
            STATUS_CODE_INDEX.get(status_code) or
            expand_unknown_status(status_code)
        )

        # WARN/ERR format: "status_code, device_name, message"
        if not status["is_ok"]:
            error_device = values[1]
            error_message = values[3] if len(values) >= 4 else values[2]

            message = "arduino_handler {}>  {}: {}".format(
                status["message"],
                error_device,
                error_message)
            rospy.logwarn(message)
            return message
        # else status: OK

        # Zip values with the corresponding environmental variable
        variable_values = values[1:]
        pairs = tuple((headers, sensor_csv_headers[headers](value))
            for headers, value in zip(sensor_csv_headers.keys()[1:], variable_values))
        return pairs
    except ValueError:
        message = "arduino_handler: Type conversion error, skipping."
        rospy.logwarn(message)
        return message
    except IndexError:
        message = "arduino_handler: Partial message: >{}<".format(line)
        rospy.logwarn(message)
        return message
    # Occasionally, we get rotten bytes which couldn't decode
    except UnicodeDecodeError:
        message = "arduino_handler: Ignoring weird bits: >{}<".format(line)
        rospy.logwarn(message)
        return message

def close_serial():
    if serial_connection is not None:
        serial_connection.close()

def connect_serial():
    timeout_s = 2 / serial_rate_hz # serial port timeout is 2x loop rate
    baud_rate = rospy.get_param("~baud_rate", 115200)

    # Initialize the serial connection
    path = "/dev/serial/by-id"
    port = None
    close_serial()
    while port is None:
        try:

            if not os.path.exists(path):
              raise Exception("No serial device found on system in {}".format(path))

            ports = [port for port in os.listdir(path) if "arduino" in port.lower()]
            if len(ports) == 0:
              raise Exception("No arduino device found on system in {}".format(path))
            port = ports[0]
            serial_connection = serial.Serial(os.path.join(path, port),
                                              baud_rate,
                                              dsrdtr = True, # Causes an Arduino soft reset
                                              timeout=timeout_s,
                                              writeTimeout=timeout_s)
            return serial_connection
        except Exception as e:
            rospy.logwarn(e)
            rospy.sleep(0.2) #seconds


if __name__ == '__main__':
    if TRACE:
        rospy.init_node('arduino_handler', log_level=rospy.DEBUG)
    else:
        rospy.init_node('arduino_handler')

    publisher_rate_hz = rospy.get_param("~publisher_rate_hz", 1)
    serial_rate_hz = rospy.get_param("~serial_rate_hz", 1)
    serial_rate = rospy.Rate(serial_rate_hz)

    serial_connection = connect_serial()

    publish_time = ros_next(publisher_rate_hz)

    arduino_delay_s = 0.25 / serial_rate_hz # Reserve 25% of loop period for Arduino comm delays

    MAX_EMPTY_READS = 4 # Arduino error messages cause empty reads, allow 4 consecutive errors
    empty_read_count = 0 # Arduino consecutive empty read counter

    while not rospy.is_shutdown():
        # These 2 are permanently on.
        actuator_state["water_aeration_pump_1"] = True
        actuator_state["water_circulation_pump_1"] = True
        # Generate the message for the current state (csv headers below):
        # status, pump1, pump2, pump3, pump4, pump5, chiller_fan,
        # chiller_pump, heater_core2, air_flush, water_aeration,
        # water_circulation, chamber_fan, blue, white, red, heater_core1,
        # chiller_compressor
        message = "0,{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16}\n".format(
            actuator_state["pump_1_nutrient_a_1"],
            actuator_state["pump_2_nutrient_b_1"],
            actuator_state["pump_3_ph_up_1"],
            actuator_state["pump_4_ph_down_1"],
            actuator_state["pump_5_water_1"],
            actuator_state["chiller_fan_1"],
            actuator_state["chiller_pump_1"],
            actuator_state["heater_core_2_1"],
            actuator_state["air_flush_1"],
            actuator_state["water_aeration_pump_1"],
            actuator_state["water_circulation_pump_1"],
            actuator_state["chamber_fan_1"],
            actuator_state["light_intensity_blue"],
            actuator_state["light_intensity_white"],
            actuator_state["light_intensity_red"],
            actuator_state["heater_core_1_1"],
            actuator_state["chiller_compressor_1"]
        ).encode('utf-8')
        buf = ""

        # Fix issue #328, sometimes serial_connection is None because of a 
        # serial port path / or error opening issue.
        if serial_connection is None:
            serial_connection = connect_serial()
        
        try:
            # Write
            serial_connection.write(message) # Write message or timeout
            trace('arduino_handler serial write %d bytes: >%s<', \
                len(message), message.replace('\n',''))
            serial_connection.flush() # Wait until all data is written
            serial_connection.flushOutput() # Clear output buffer
            # Read. Arduino sends both error messages and sensor data, 
            # in that order, and both may be in the buffer.
            # Wait until Arduino data is stable 
            # (rospy.Rate will still try to keep the loop at serial_rate_hz)
            rospy.sleep(arduino_delay_s)
            # Blocks until one line is read or times out
            buf = serial_connection.readline() 
            # Count consecutive empty reads, raise exception if threshold is exceeded
            if buf == "":
                empty_read_count += 1
            else:
                empty_read_count = 0
            trace('arduino_handler empty read count: %d', empty_read_count)
            if empty_read_count > MAX_EMPTY_READS:
                empty_read_count = 0
                raise Exception("arduino_handler: serial_connection.readline() broken")
            """
            Since errors are sent first, the readline may have gotten an
            Arduino error message and not sensor data.  Therefore the flush
            below will throw away sensor data if it was sent after the error
            message.
            Without the flush the input buffer eventually will overflow if
            enough error messages are sent by the Arduino.  
            """
            serial_connection.flushInput()
        except serial.serialutil.SerialException as e1:
            # This usually happens when the serial port gets closed or switches
            rospy.logwarn(e1)
            serial_connection = connect_serial()
        except serial.serialutil.SerialTimeoutException as e2:
            # Exception that is raised on write timeouts
            rospy.logwarn(e2)
            serial_connection = connect_serial()
        except Exception as e3:
            # Exception triggered by too many consecutive empty reads
            rospy.logwarn(e3)
            serial_connection = connect_serial()

        pairs_or_error = process_message(buf)
        if type(pairs_or_error) is str:
            error_message = pairs_or_error
            ARDUINO_STATUS_PUBLISHER.publish(error_message)
        else:
            pairs = pairs_or_error
            for header, value in pairs:
                sensor_state[header] = value

        if publish_time():
            #trace("arduino_handler publish_time")
            if type(pairs_or_error) is not str:
                ARDUINO_STATUS_PUBLISHER.publish("OK")
            for variable in sensor_state:
                if variable not in [v.name for v in VALID_SENSOR_VARIABLES]:
                    continue
                PUBLISHERS[variable].publish(sensor_state[variable])
        serial_rate.sleep()
        # end of while loop

    close_serial()
    # end of main
