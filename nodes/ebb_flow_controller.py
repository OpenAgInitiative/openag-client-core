#!/usr/bin/env python
"""
ebb_flow_controller.py

This software module is a module that will oscillate between on/off
at "on_time" seconds and "off_time" second intervals.
It works much like direct_controller.py but it oscillates. 

Usage (launchfile):
<node pkg="openag_brain" type="ebb_flow_controller.py" name="air_flush_on_controller_1">
    <param name="variable" value="env_var" type="str"/>
    <param name="on_time" value="0" type="int"/>    <!-- seconds -->
    <param name="off_time" value="0" type="int"/>   <!-- seconds -->
</node>
"""
import rospy
import time, sched
from std_msgs.msg import Float64

if __name__ == '__main__':
    rospy.init_node('ebb_flow_controller')

    # Make sure that we're under an environment namespace.
    namespace = rospy.get_namespace()
    if namespace == '/':
        raise RuntimeError(
            "Cannot be run in the global namespace. Please "
            "designate an environment for this module."
        )

    command_pub_name = "cmd"
    state_pub_name = "state"



    variable = rospy.get_param("~variable", None)
    if variable is not None:
        command_pub_name = "{}/commanded".format(variable)
        state_pub_name = "{}/measured".format(variable)

    # Node will publish to ~variable/commanded and ~variable/measured
    command_pub = rospy.Publisher(command_pub_name, Float64, queue_size=10)
    state_pub = rospy.Publisher(state_pub_name, Float64, queue_size=10)

    def publish_both(item):
        command_pub.publish(item)
        state_pub.publish(item)

    is_on = False # Boolean value, True is ON and False is OFF
    prev_time = rospy.get_time()
    current_duration = 0
    rate = rospy.Rate(1)
    while not rospy.is_shutdown(): # Run while ROS is running
        on_time = rospy.get_param("~on_time", None)
        off_time = rospy.get_param("~off_time", None)

        if on_time is None or off_time is None:
            rospy.logerr("on_time or off_time is not set for this module.")
            continue
        now_time = rospy.get_time()
        current_duration = now_time - prev_time
        prev_time = now_time

        next_timeout = off_time if is_on else on_time
        if current_duration >= next_timeout:
            is_on = not is_on
            current_duration = 0

        bool_to_float = 1.0 if is_on else 0.0
        publish_both(bool_to_float)
        rate.sleep()
