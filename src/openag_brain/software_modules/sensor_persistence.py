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

import rospy
import rostopic
from couchdb import Server
from std_msgs.msg import Float64

from openag.cli.config import config as cli_config
from openag.models import EnvironmentalDataPoint
from openag.db_names import ENVIRONMENTAL_DATA_POINT
from openag_brain.var_types import SENSOR_VARIABLES
from openag_brain.utils import read_environment_from_ns

def should_update_point(
    last_value, value
    delta_time, min_update_interval, max_update_interval
    ):
    if delta_time < min_update_interval:
        return False
    if delta_time < max_update_interval:
        delta_val = value - last_value
        if abs(delta_val / last_value) <= 0.01:
            return False
    return True

def read_index_key(environment, variable, is_desired):
    """Given a point, returns a key suitable for indexing that point"""
    point_type = "desired" if is_desired else "measured"
    key = "{}_{}_{}".format(environment, point_type, variable)
    return key

class TopicPersistence:
    def __init__(
        self, db, topic, topic_type, environment, variable, is_desired,
        max_update_interval, min_update_interval
    ):
        self.db = db
        self.environment = environment
        self.variable = variable
        self.is_desired = is_desired
        self.last_points = {}
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

        # Find previous datapoint (if any)
        key = read_index_key(self.environment, self.variable, self.is_desired)
        last_point = self.last_points.get(key)

        # Throttle updates
        delta_time = curr_time - self.last_time
        if last_point and not should_update_point(
            last_point.value, value,
            delta_time, self.min_update_interval, self.max_update_interval
        ):
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

        # Store point in index so we can compare against it later
        self.last_points[key] = point

    def gen_doc_id(self, curr_time):
        return "{}-{}".format(curr_time, random.randint(0, sys.maxsize))

def create_persistence_objects(
    server, environment_id, max_update_interval, min_update_interval
):
    env_var_db = server[ENVIRONMENTAL_DATA_POINT]
    for variable, MsgType in SENSOR_VARIABLES:
        variable = str(variable)
        topic = "{}/measured".format(variable)
        TopicPersistence(
            topic=topic, topic_type=Float64,
            environment=environment_id,
            variable=variable, is_desired=False,
            db=env_var_db, max_update_interval=max_update_interval,
            min_update_interval=min_update_interval
        )

if __name__ == '__main__':
    db_server = cli_config["local_server"]["url"]
    if not db_server:
        raise RuntimeError("No local database specified")
    server = Server(db_server)
    rospy.init_node('sensor_persistence')
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
    environment_id = read_environment_from_ns(rospy.get_namespace())
    create_persistence_objects(
        server, environment_id,
        max_update_interval=max_update_interval,
        min_update_interval=min_update_interval
    )
    rospy.spin()
