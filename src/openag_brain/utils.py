import os
import rospkg
from sys import maxsize
from random import randint
from re import match
import json


def resolve_fixtures(fixtures):
    """
    Given a list of fixture names, returns a list of fully resolved fixture
    paths.
    """
    rospack = rospkg.RosPack()
    pkg_path = rospack.get_path('openag_brain')
    fixtures_path = os.path.join(pkg_path, "fixtures")
    resolved = [os.path.join(fixtures_path, fixture_name + ".json") for fixture_name in fixtures]
    return resolved

def gen_doc_id(curr_time):
    """
    Given a unix time, generate a unique ID string with extremely low chance
    of collision.

    Returns a string.
    """
    return "{}-{}".format(curr_time, randint(0, maxsize))

def read_environment_from_ns(namespace):
    """
    Given a ROS topic name, attempt to match an environment ID in topic
    namespace.

    Use:

        read_environment_from_ns(rospy.get_namespace())
    """
    result = match("/environments/(\w+)/", namespace)
    if not result:
        raise ValueError(
            "No environment id found in namespace \"{}\".".format(namespace)
        )
    environment_id = result.group(1)
    return environment_id
