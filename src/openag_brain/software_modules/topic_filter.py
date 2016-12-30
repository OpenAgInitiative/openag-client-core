#!/usr/bin/python
import rospy
import rosgraph

from re import match
from roslib.message import get_message_class

class EWMA:
    def __init__(self, a):
        self.a = a
        self.average = None

    def __call__(self, sample):
        # Update the average
        if self.average is None:
            self.average = sample
            return
        self.average = self.a * sample + (1 - self.a) * self.average

def filter_topic(src_topic, dest_topic, topic_type):
    rospy.loginfo("Filtering topic {} to topic {}".format(
        src_topic, dest_topic
    ))
    pub = rospy.Publisher(dest_topic, topic_type, queue_size=10)
    f = EWMA(0.3)
    def callback(src_item):
        f(src_item.data)
        dest_item = topic_type(f.average)
        pub.publish(dest_item)
    sub = rospy.Subscriber(src_topic, topic_type, callback)
    return sub, pub

def gen_parsed_measured(pubs):
    """
    Generate a description tuple for topics that measured endpoints.
    Matches, filters and parses topic names to find measured information.
    """
    for topic, topic_type in pubs:
        result = match("/environments/(\w+)/measured/(\w+)", topic)
        if result:
            environment_id = result.groups(1)
            variable = result.groups(2)
            yield (topic, topic_type, environment_id, variable)

def filter_all_topics(pubs):
    """
    Given an iterator publishers, where each publisher is a two-tuple
    `(topic, type)`, publishes a filtered topic endpoint.
    """
    for topic, topic_type, environment_id, variable in gen_parsed_measured(pubs):
        TopicType = get_message_class(topic_type)
        dest_topic = "/environments/{}/filtered/{}".format(
            environment_id,
            variable
        )
        filter_topic(topic, dest_topic, TopicType)

if __name__ == '__main__':
    rospy.init_node("topic_filter")
    rostopic_master = rosgraph.Master("/rostopic")
    pubs, subs, _ = rostopic_master.getSystemState()
    filter_all_topics(pubs)
    rospy.spin()
