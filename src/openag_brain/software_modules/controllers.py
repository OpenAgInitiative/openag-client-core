#!/usr/bin/env python
"""
Base classes for control modules. To be used as a class inherited.

The `output_type` class attribute has to be set if the controller output is not
Float64, which is set as default.

If arguments are defined in the `__init__` method, they will be
loaded automatically from the private ROS params defined in the
launchfile.

1. Open-Loop Controllers

Implement an `update(self, set_point)` function that given the current setpoint
and arbirary internal state commands a new output value.

Subscribes to the setpoint ROS topic:

    Set point  - /<variable>/desired

Every time a setpoint is received by the controller, the `update` function
will be called to calculate the new commanded output.
The value is published to the following ROS topics:

    State      - /<variable>/measured
    Output     - /<variable>/commanded

See direct_controller.py for a sample implementation of an open-loop controller

------------

2. Closed-Loop Controllers:

Implement an `update(self, state)` function that given the current set point,
and arbirary internal state including the set_point, a commanded value is
calculated. This type of controller only updates the commanded value when a
new measurement is received, not when the set point is defined.

Internally, it sets up:

Subscribes to the setpoint and measurement ROS topics.

    Set point  - /<variable>/desired
    State      - /<variable>/measured

Every time a measurement is received by the controller, the `update` function
will be called to calculate the new commanded output.
The value is published to the following ROS topic:

    Output     - /<variable>/commanded

See on_off_controller.py for an implementation of a closed-loop controller
"""
import rospy
from re import sub
from inspect import getargspec
from std_msgs.msg import Float64

class Controller(object):
    set_point = None
    output_type = Float64

    @staticmethod
    def start(cls):
        node_name = to_snake_case(cls.__name__)
        rospy.init_node(node_name)
        # Make sure that we're under an environment namespace.
        namespace = rospy.get_namespace()
        if namespace == '/':
            raise RuntimeError(
                "Cannot be run in the global namespace. Please "
                "designate an environment for this module."
            )

        # Get args of the initializer.
        # The first arg is the instance, so just extract the rest
        # Note: *args or **kwargs won't be used
        param_values = {}
        try:
            param_names = getargspec(cls.__init__).args[1:]
            for param_name in param_names:
                private_param_name = "~" + param_name
                if rospy.has_param(private_param_name):
                    param_values[param_name] = rospy.get_param(
                        private_param_name
                    )
        except TypeError:
            # raised by getargspec if no __init__ is defined,
            # which means there are no custom init params
            pass

        controller = cls(**param_values)

        cmd_topic = "cmd"
        measured_topic = "state"
        desired_topic = "desired"

        variable = rospy.get_param("~variable", None)
        if variable is not None:
            cmd_topic = "{}/commanded".format(variable)
            measured_topic = "{}/measured".format(variable)
            desired_topic = "{}/desired".format(variable)

        rospy.logdebug("Starting {} controller for {}".format(
            node_name, variable
        ))
        return controller, cmd_topic, measured_topic, desired_topic

class ClosedLoopController(Controller):
    def update(self, state):
        raise NotImplementedError(
            "Must `def update(self, state):` to use this base class"
        )

    @classmethod
    def start(cls):
        controller, cmd_topic, measured_topic, desired_topic = Controller.start(cls)
        cmd_pub = rospy.Publisher(cmd_topic, cls.output_type, queue_size=10)

        def state_callback(item):
            cmd = controller.update(item.data)
            if cmd is not None:
                cmd_pub.publish(cmd)

        def set_point_callback(item):
            controller.set_point = item.data

        state_sub = rospy.Subscriber(measured_topic, Float64, state_callback)
        set_point_sub = rospy.Subscriber(
            desired_topic, Float64, set_point_callback
        )

        rospy.spin()

class OpenLoopController(Controller):
    def update(self, set_point):
        raise NotImplementedError(
            "Must `def update(self, set_point):` to use this base class"
        )

    @classmethod
    def start(cls):
        controller, cmd_topic, measured_topic, desired_topic = Controller.start(cls)
        cmd_pub = rospy.Publisher(cmd_topic, cls.output_type, queue_size=10)
        measured_pub = rospy.Publisher(
            measured_topic, cls.output_type, queue_size=10
        )

        def set_point_callback(item):
            cmd = controller.update(item.data)
            if cmd is not None:
                cmd_pub.publish(cmd)
                # Also re-publish command as measurement so it can be persisted
                # as environmental data point
                # TODO transform Bool cmds to proper fake measurement types
                measured_pub.publish(cmd)

        set_point_sub = rospy.Subscriber(
            desired_topic, Float64, set_point_callback
        )

        rospy.spin()

# Convert CamelCase to snake_case
# From http://stackoverflow.com/a/1176023/756000
def to_snake_case(name):
    s1 = sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
