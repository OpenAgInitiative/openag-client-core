#!/usr/bin/python
"""
The `sensor_persistence.py` module listens for measurements of the ambient
conditions of an environment and writes those measurements to the CouchDB
instance. There should be exactly one instance of this module per environment
in the system.
"""

import sys
import time
import random
from re import match

import rospy
import rostopic
import rosgraph

from roslib.message import get_message_class

class TopicPersistence:
    def __init__(
        self, db, topic, topic_type, environment, variable, is_desired,
        max_update_interval, min_update_interval
    ):
        self.db = db
        self.environment = environment
        self.variable = variable
        self.is_desired = is_desired
        self.last_value = None
        self.last_time = 0
        self.sub = rospy.Subscriber(topic, topic_type, self.on_data)
        self.max_update_interval = max_update_interval
        self.min_update_interval = min_update_interval

    def on_data(self, item):
        curr_time = time.time()
        value = item.data
        # This is kind of a hack to correctly interpret UInt8MultiArray
        # messages. There should be a better way to do this
        if item._slot_types[item.__slots__.index('data')] == "uint8[]":
            value = [ord(x) for x in value]

        # Throttle updates
        delta_time = curr_time - self.last_time
        if delta_time < self.min_update_interval:
            return
        if delta_time < self.max_update_interval and self.last_value:
            delta_val = value - self.last_value
            if abs(delta_val / self.last_value) <= 0.01:
                return

        # Save the data point
        point = EnvironmentalDataPoint({
            "environment": self.environment,
            "variable": self.variable,
            "is_desired": self.is_desired,
            "value": value,
            "timestamp": curr_time
        })
        point_id = self.gen_doc_id(curr_time)
        self.db[point_id] = point

        self.last_value = value
        self.last_time = curr_time

    def gen_doc_id(self, curr_time):
        return "{}-{}".format(curr_time, random.randint(0, sys.maxsize))

def gen_parsed_filtered(pubs):
    """
    Generate a description tuple for topics that measured endpoints.
    Matches, filters and parses topic names to find measured information.
    """
    for topic, topic_type in pubs:
        result = match("/environments/(\w+)/filtered/(\w+)", topic)
        if result:
            environment_id = result.groups(1)
            variable = result.groups(2)
            yield (topic, topic_type, environment_id, variable)

def create_persistence_objects(
    pubs, max_update_interval, min_update_interval
):
    for topic, topic_type, environment_id, variable in gen_parsed_filtered(pubs):
        TopicType = get_message_class(topic_type)
        TopicPersistence(
            topic=topic, topic_type=TopicType,
            environment=environment_id,
            variable=variable, is_desired=False,
            db=env_var_db, max_update_interval=max_update_interval,
            min_update_interval=min_update_interval
        )

if __name__ == '__main__':
    rospy.init_node('sensor_persistence')

    rostopic_master = rosgraph.Master("/rostopic")
    pubs, subs, _ = rostopic_master.getSystemState()

    try:
        max_update_interval = rospy.get_param("~max_update_interval")
    except KeyError:
        rospy.logwarn(
            "No maximum update interval specified for sensor persistence "
            "module"
        )
        max_update_interval = 600
    try:
        min_update_interval = rospy.get_param("~min_update_interval")
    except KeyError:
        rospy.logwarn(
            "No minimum update interval specified for sensor persistence "
            "module"
        )
        min_update_interval = 5
    create_persistence_objects(
        pubs,
        max_update_interval=max_update_interval,
        min_update_interval=min_update_interval
    )
    rospy.spin()
