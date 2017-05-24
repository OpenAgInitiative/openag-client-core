#!/usr/bin/env python
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

    on_time = rospy.get_param("~on_time", None)
    off_time = rospy.get_param("~off_time", None)

    if on_time is None or off_time is None:
        raise RuntimeError(
            "There is no on_time or off_time set for this module."
        )

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

    on_off_state = False # Boolean value, True is ON and False is OFF
    time_to_next_state = off_time
    time = rospy.get_time()
    rate = rospy.Rate(1)
    while not rospy.is_shutdown(): # Run while ROS is running
        time_to_next_state -= (rospy.get_time() - time)
        time = rospy.get_time()
        if time_to_next_state <= 0:
            on_off_state = not on_off_state
            time_to_next_state = on_time if on_off_state else off_time
        bool_to_float = 1.0 if on_off_state else 0.0
        publish_both(bool_to_float)
        rate.sleep()
