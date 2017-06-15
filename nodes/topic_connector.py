#!/usr/bin/python
"""
By convention, firmware modules publish sensor data to ROS topics in the
namespace `/sensors` and listen to actuator commands on ROS topics in the
namespace `/actuators`. This is very useful for low level tasks such as
debugging/testing your hardware but not so useful for getting a high level
overview of the environmental conditions of your system. For this, we would
like to use topics namespaced by the ID of the environment on which the piece
of hardware acts (e.g. /environment_1/measured/air_temperature). This module
connects topics so as to ensure that both of these system views work as
expected. There should be exactly one instance of this module in the system
"""
import rospy
import rosgraph
import rostopic

# You MUST import this msg package BEFORE any internal 'openag_brain' python
# code.  Or you will get "ImportError: No module named msg".
from openag_brain.msg import SensorInfo
from openag_lib.firmware.util import synthesize_firmware_module_info
from openag_brain.models import FirmwareModule, FirmwareModuleType
from std_msgs.msg import Bool, Float32, Float64
from roslib.message import get_message_class

def connect_topics(
    src_topic, dest_topic, src_topic_type, dest_topic_type, multiplier=1,
    deadband=0
):
    rospy.loginfo("Connecting topic {} to topic {}".format(
        src_topic, dest_topic
    ))
    pub = rospy.Publisher(dest_topic, dest_topic_type, queue_size=10)
    def callback(src_item):
        val = src_item.data
        val *= multiplier
        if dest_topic_type == Bool:
            val = (val > deadband)
        dest_item = dest_topic_type(val)
        pub.publish(dest_item)
    sub = rospy.Subscriber(src_topic, src_topic_type, callback)
    return sub, pub

def connect_sensor_info_topics(src_topic, dest_topic):
    rospy.loginfo("Connecting topic {} to topic {}".format(
        src_topic, dest_topic
    ))
    pub = rospy.Publisher(dest_topic, SensorInfo, queue_size=1, latch=True)
    sub = rospy.Subscriber(src_topic, SensorInfo, pub.publish)

def connect_all_topics(firmware_module, firmware_module_type):
    modules = {
        record["_id"]: FirmwareModule(record) for record in
        firmware_module if not record["_id"].startswith('_')
    }
    module_types = {
        record["_id"]: FirmwareModuleType(record) for record in
        firmware_module_type if not record["_id"].startswith("_")
    }
    modules = synthesize_firmware_module_info(modules, module_types)
    for module_id, module_info in modules.items():
        for input_name, input_info in module_info["inputs"].items():
            if not "actuators" in input_info["categories"]:
                continue
            src_topic = "/environments/{}/{}/commanded".format(
                module_info["environment"], input_info["variable"]
            )
            dest_topic = "/actuators/{}/{}".format(module_id, input_name)
            dest_topic_type = get_message_class(input_info["type"])
            src_topic_type = Float64
            connect_topics(
                src_topic, dest_topic, src_topic_type, dest_topic_type,
                multiplier=input_info.get("multiplier", 1),
                deadband=input_info.get("deadband", 0)
            )
        for output_name, output_info in module_info["outputs"].items():
            if not "sensors" in output_info["categories"]:
                continue
            src_topic = "/sensors/{}/{}/raw".format(module_id, output_name)
            dest_topic = "/environments/{}/{}/raw".format(
                module_info["environment"], output_info["variable"]
            )
            src_topic_type = get_message_class(output_info["type"])
            dest_topic_type = Float64
            connect_topics(
                src_topic, dest_topic, src_topic_type, dest_topic_type
            )
            src_info_topic = "/sensors/{}/{}/info".format(
                module_id, output_name
            )
            dest_info_topic = "/environments/{}/{}/info".format(
                module_info["environment"], output_info["variable"]
            )
            connect_sensor_info_topics(src_info_topic, dest_info_topic)

if __name__ == '__main__':
    rospy.init_node("topic_connector")
    firmware_module = rospy.get_param("/firmware_module")
    firmware_module_type = rospy.get_param("/firmware_module_type")
    connect_all_topics(firmware_module, firmware_module_type)
    rospy.spin()
