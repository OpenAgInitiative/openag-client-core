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

from openag_lib.db_bootstrap.db_names import ENVIRONMENTAL_DATA_POINT
from openag_lib.config import config as cli_config
from openag_brain.models import EnvironmentalDataPoint
from openag_brain.utils import read_environment_from_ns
from openag_brain.load_env_var_types import create_variables

# Filter a list of environmental variables that are specific to environment
# sensors and actuators
ENVIRONMENT_VARIABLES = create_variables(rospy.get_param('/var_types/environment_variables'))

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

def create_persistence_objects(
    server, environment_id, max_update_interval, min_update_interval
):
    env_var_db = server[ENVIRONMENTAL_DATA_POINT]
    for variable in ENVIRONMENT_VARIABLES.itervalues():
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
