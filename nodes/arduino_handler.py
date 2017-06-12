#!/usr/bin/python
"""
This ROS node Handles Arduino messages and publishes them to ROS topics
It also receives env_var/commanded topics and sends messages to the Arduino accordingly.


Usage (in ROS launchfile):
<node pkg="openag_brain" type="arduino_handler.py" name="arduino_handler">
  <param name="serial_port_id" value="/dev/ttyACM0" type="str"/>
  <param name="publisher_rate_hz" value="1" type="int"/>
  <param name="baud_rate" value="115200" type="int"/>
</node>
"""
import serial
import rospy
from std_msgs.msg import String
from roslib.message import get_message_class
from openag_brain.load_env_var_types import VariableInfo

# below: immutables/consts
# csv_headers will be hard coded since it will be tightly coupled with Arduino sketch anyways.
# the associated types are also included in the tuple since it is usually relevant to have around.
sensor_csv_headers = (
    ("status", int),
    ("air_humidity", float),
    ("air_temperature", float),
    ("air_carbon_dioxide", float),
    ("water_temperature", float),
    ("water_level_low", bool),
    ("water_level_high", bool),
    ("water_potential_hydrogen", float),
    ("water_electrical_conductivity", float)
)

actuator_csv_headers =  (
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
)

actuator_listen_variables = (
    "air_temperature",
    "water_potential_hydrogen",
    "nutrient_flora_duo_a",
    "nutrient_flora_duo_b",
    "air_flush_on",
    "light_intensity_red",
    "light_intensity_blue",
    "light_intensity_white",
    "water_level_high"
)

ENVIRONMENTAL_VARIABLES = frozenset(
    VariableInfo.from_dict(d)
    for d in rospy.get_param("/var_types/environment_variables").itervalues())

VALID_SENSOR_VARIABLES = [v for v in ENVIRONMENTAL_VARIABLES
    if v.name in [t[0] for t in sensor_csv_headers]]

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

# These are callbacks that map the */commanded topic to the Arduino actuators.
# This is a job that was traditionally done by topic_connector.py, but
# these are hardcoded configurations even though the configuration is in the
# personal_food_computer_v2.yaml file because we removed the codegen from
# `firmware`, and you would need to rewrite both this node and the config file if
# you changed the topic mapping.
# This direct mapping will also let the future `actuator_node`
# for single actuators to listen in on */commanded topics and decide to actuate
# based on the information individually instead of having to write a config.
# 6/7/2017 Rikuo Hasegawa(Spaghet)
def air_temperature_callback(msg): # float -1~1
    command = msg.data
    up = (
        ("heater_core_2_1", bool),
        ("heater_core_1_1", bool)
    )
    down = (
        ("chiller_fan_1", bool),
        ("chiller_pump_1", bool),
        ("chiller_compressor_1", bool)
    )
    always = (
        ("chamber_fan_1", bool),
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
    up = ("pump_3_ph_up_1", bool)
    down = ("pump_4_ph_down_1", bool)

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
    command = msg.data
    actuator_state["pump_1_nutrient_a_1"] = command


def nutrient_flora_duo_b_callback(msg): # float
    command = msg.data
    actuator_state["pump_2_nutrient_b_1"] = command


def air_flush_on_callback(msg): # float 0/1
    command = msg.data
    actuator_state["air_flush_1"] = bool(command)


def light_intensity_blue_callback(msg): # float 0~1
    command = msg.data
    actuator_state["light_intensity_blue"] = command


def light_intensity_white_callback(msg): # float 0~1
    command = msg.data
    actuator_state["light_intensity_white"] = command


def light_intensity_red_callback(msg): # float 0~1
    command = msg.data
    actuator_state["light_intensity_red"] = command


# The water level sensor is HIGH when dry, which gets passed through the
# linear_controller node, which takes the sensor value */measured
# and passes it as */commanded. We should set the pump_5_water_1 to HIGH when
# we receive a True here. I want to deprecate this with something more
# feedback loop oriented: https://github.com/OpenAgInitiative/openag_brain/issues/270
def water_level_high_callback(msg): # Bool
    command = msg.data
    if command:
        actuator_state["pump_5_water_1"] = True

CALLBACKS = {
    "air_temperature":          air_temperature_callback,
    "water_potential_hydrogen": water_potential_hydrogen_callback,
    "nutrient_flora_duo_a":     nutrient_flora_duo_a_callback,
    "nutrient_flora_duo_b":     nutrient_flora_duo_b_callback,
    "air_flush_on":             air_flush_on_callback,
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

def expand_unknown_status(status_code):
    return {
        "is_ok": False,
        "message": "Unknown status code {}".format(status_code)
    }

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

# Read the serial message string, and publish to the correct topics
def process_message(line):
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
        # status: OK

        # Zip values with the corresponding environmental variable
        variable_values = values[1:]
        pairs = tuple((headers[0], headers[1](value))
            for headers, value in zip(sensor_csv_headers[1:], variable_values))
        return pairs
    except ValueError:
        message = "Type conversion error, skipping."
        rospy.logwarn(message)
        return message
    except IndexError:
        message = "Short read, received part of a message: {}".format(buf.decode())
        rospy.logwarn(message)
        serial_connection.close()
        serial_connection.open()
        return message
    # Occasionally, we get rotten bytes which couldn't decode
    except UnicodeDecodeError:
        message = "Received weird bits, ignoring: {}".format(buf)
        rospy.logwarn(message)
        serial_connection.close()
        serial_connection.open()
        return message

if __name__ == '__main__':
    rospy.init_node('handle_arduino')

    serial_port_id = rospy.get_param("~serial_port_id", "/dev/ttyACM0")
    publisher_rate_hz = rospy.get_param("~publisher_rate_hz", 1)
    baud_rate = rospy.get_param("~baud_rate", 115200)

    timeout_s = 1 / publisher_rate_hz
    # below: mutables (gasp!)
    # Initialize the serial connection
    serial_connection = serial.Serial(serial_port_id, baud_rate, timeout=timeout_s)

    # Latest actuator and sensor states we are aware of.
    actuator_state = {
        header: type_constructor()
        for header, type_constructor in actuator_csv_headers
    }
    sensor_state = {}

    # These 2 are permanently on.
    actuator_state["water_aeration_pump_1"] = True
    actuator_state["water_circulation_pump_1"] = True


    publish_time = ros_next(publisher_rate_hz)
    while not rospy.is_shutdown():
        # Read before writing
        buf = serial_connection.readline()

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
        rospy.logwarn(message)
        serial_connection.write(message)
        serial_connection.flush()

        pairs_or_error = process_message(buf)
        if type(pairs_or_error) is str:
            error_message = pairs_or_error
            ARDUINO_STATUS_PUBLISHER.publish(error_message)
        else:
            pairs = pairs_or_error
            for header, value in pairs:
                sensor_state[header] = value

        if publish_time():
            if type(pairs_or_error) is not str:
                ARDUINO_STATUS_PUBLISHER.publish("OK")
            for variable in sensor_state:
                if variable not in [v.name for v in VALID_SENSOR_VARIABLES]:
                    continue
                PUBLISHERS[variable].publish(sensor_state[variable])

    serial_connection.close()
