#!/usr/bin/env python
"""
The `api.py` module defines an API that allows clients to interact with ROS
over HTTP. It is accessible at `<hostname>:5984/_openag/` when the project is
running. There should always be exactly one instance of this module in the
system.
"""
import gevent.monkey; gevent.monkey.patch_all()

import socket

import rospy
import rostopic
import rosgraph
import rosservice
from roslib.message import get_message_class
from flask import Flask, jsonify, request, Response
from gevent.wsgi import WSGIServer
from gevent.queue import Queue

API_VER = "0.0.1"

app = Flask(__name__)
app.debug = True

@app.errorhandler(socket.error)
@app.errorhandler(rosservice.ROSServiceIOException)
def socket_error_handler(e):
    return error("Unable to communicate with master")

def error(msg, status_code=400):
    return jsonify({"error": str(msg)}), status_code

def success(msg, status_code=200):
    return jsonify({"message": str(msg)}), status_code

rostopic_master = rosgraph.Master("/rostopic")
rosnode_master = rosgraph.Master("/rosnode")

@app.route("/api/{v}/param".format(v=API_VER), methods=["GET"])
def list_params():
    """
    GET /api/<version>/param

    GET a list of all available params from the ROS Parameter Server.
    See http://wiki.ros.org/Parameter%20Server for more on the Parameter Server.

    Parameter names are listed in the "results" field of the JSON response body.
    """
    return jsonify({"results": rospy.get_param_names()})

@app.route("/api/{v}/param/<path:param_name>".format(v=API_VER), methods=["GET"])
def get_param(param_name):
    """
    GET /api/<version>/param/<param_name>

    GET the value for a specific parameter at param_name in the ROS
    Parameter Server.

    Parameter value is in the "result" field of the JSON response body. If
    parameter does not exist, a JSON document with ERROR field will
    be returned.
    """
    if not rospy.has_param(param_name):
        return error("No such parameter exists")
    return jsonify({"result": str(rospy.get_param(param_name))})

@app.route("/api/{v}/param/<path:param_name>".format(v=API_VER), methods=["POST"])
def set_param(param_name):
    """
    POST /api/<version>/param/<param_name> {"value": "x"}

    POST to the ROS Parameter Server. Value should be in the value field
    of the request body.
    """
    if not "value" in request.values:
        return error("No value supplied")
    rospy.set_param(param_name, request.values["value"])
    return "", 204

@app.route("/api/{v}/service".format(v=API_VER), methods=["GET"])
def list_services():
    """
    GET /api/<version>/service

    GET a list of all available ROS services.

    Services are listed in the "results" field of the JSON response body.
    """
    return jsonify({"results": rosservice.get_service_list()})

@app.route("/api/{v}/service/<path:service_name>".format(v=API_VER), methods=["GET"])
def get_service_info(service_name):
    """
    GET /api/<version>/service/<service_name>

    GET information about a ROS service.
    """
    service_name = "/" + service_name
    service_type = rosservice.get_service_type(service_name)
    if not service_type:
        return error("No such service exists")
    return jsonify({
        "request_type": service_type,
        "node": rosservice.get_service_node(service_name),
        "args": rosservice.get_service_args(service_name).split(" ")
    })

@app.route("/api/{v}/service/<path:service_name>".format(v=API_VER), methods=["POST"])
def perform_service_call(service_name):
    """
    POST /api/<version>/service/<service_name>

    POST to a service to change it somehow. service_name may be a path.

    For example, to start an environmental recipe in an environment, use the
    start_recipe service:

        POST /api/<version>/service/<environment_id>/start_recipe {"recipe_id": <id>}
    """
    # Add leading slash to service_name. ROS qualifies all services with a
    # leading slash.
    service_name = '/' + service_name
    # Find the class that ROS autogenerates from srv files that is associated
    # with this service.
    try:
        ServiceClass = rosservice.get_service_class_by_name(service_name)
    except rosservice.ROSServiceException as e:
        return error(e)
    # If we made it this far, the service exists.
    # Wait for service to be ready before attempting to use it.
    try:
        rospy.wait_for_service(service_name, 1)
    except rospy.ROSException as e:
        raise socket.error()
    # Get JSON args if they exist. If they don't, treat as if empty array
    # was passed.
    json = request.get_json(silent=True)
    args = json if json else []
    service_proxy = rospy.ServiceProxy(service_name, ServiceClass)
    try:
        # Unpack the list of args and pass to service_proxy function.
        res = service_proxy(*args)
    except (rospy.ServiceException, TypeError) as e:
        return error(e)
    status_code = 200 if getattr(res, "success", True) else 400
    data = {k: getattr(res, k) for k in res.__slots__}
    return jsonify(data), status_code

@app.route("/api/{v}/topic".format(v=API_VER), methods=["GET"])
def list_topics():
    """
    GET /api/<version>/topic

    GET the list of published ROS topics.
    """
    state = rostopic_master.getSystemState()
    pubs, subs, _ = state
    topics = set(x[0] for x in subs) | set(x[0] for x in pubs)
    return jsonify({"results": list(topics)})

@app.route("/api/{v}/topic/<path:topic_name>".format(v=API_VER), methods=["GET"])
def get_topic_info(topic_name):
    """
    GET /api/<version>/topic/<topic_name>

    GET info from a ROS topic.

    Returns a JSON response with the following fields (or error):

    {
        "type": "...",   // topic type, \n
        "subs": [...],   // a list of subscribers \n
        "pubs": [...]    // a list of publishers \n
    }
    """
    topic_name = "/" + topic_name
    state = rostopic_master.getSystemState()
    pubs, subs, _ = state
    topic_exists = 2
    try:
        subs = next(x for x in subs if x[0] == topic_name)[1]
    except StopIteration:
        topic_exists -= 1
        subs = []
    try:
        pubs = next(x for x in pubs if x[0] == topic_name)[1]
    except StopIteration:
        topic_exists -= 1
        pubs = []
    if not topic_exists:
        return error("Topic does not exist", 404)
    topic_type = next(
        x for name, x in rostopic_master.getTopicTypes() if name == topic_name
    )
    return jsonify({
        "type": topic_type,
        "subs": subs,
        "pubs": pubs
    })

@app.route("/api/{v}/topic/<path:topic_name>".format(v=API_VER), methods=["POST"])
def post_topic_message(topic_name):
    """
    POST /api/<version>/topic/<topic_name>

    POST a message to a ROS topic by name.

    Requires a JSON payload of shape: ``[x, y, z]``. The values of the JSON
    array must match the argument types of the topic's type constructor.
    """
    topic_name = "/" + topic_name
    # Get the list of ROS topics in the system.
    # Returns a list of [topic, type_string] pairs.
    topic_list = rostopic_master.getTopicTypes()
    # Find topic in list (this is Python's approach to find).
    try:
        topic_match = next(x for x in topic_list if x[0] == topic_name)
    except StopIteration:
        # If we can't find the topic, return early (400 bad request).
        return error("Topic does not exist")
    json = request.get_json(silent=True)
    args = json if json else []
    try:
        # Get the message type constructor for the topic's type string.
        MsgType = get_message_class(topic_match[1])
        pub = rospy.Publisher(topic_name, MsgType, queue_size=10)
        # Unpack JSON list and pass to publish.
        # pub.publish() will pass the list of arguments to the message
        # type constructor.
        pub.publish(*args)
    except Exception, e:
        return error("Wrong arguments for topic type constructor")
    return success("Posted message to topic")

@app.route("/api/{v}/topic_stream/<path:topic_name>".format(v=API_VER), methods=["GET"])
def stream_topic(topic_name):
    """
    GET /api/<version>/topic_stream/<topic_name>

    Stream a topic over HTTP by keeping the http connection alive.
    """
    topic_name = "/" + topic_name
    try:
        msg_class, real_topic, _ = rostopic.get_topic_class(topic_name)
    except rostopic.ROSTopicIOException as e:
        raise e
    if not real_topic:
        return error("Topic does not exist", 404)
    queue = Queue(5)
    def callback(dataIn, queue=queue):
        data = getattr(dataIn, "data", None)
        if data is None:
            data = {"header": getattr(dataIn, "header"), "status": getattr(dataIn, "status")}
        queue.put(data)
    sub = rospy.Subscriber(real_topic, msg_class, callback)
    def gen(queue=queue):
        while True:
            x = queue.get()
            yield str(x) + "\n"
    return Response(gen(),  mimetype='text/plain')

@app.route("/api/{v}/topic_data/<path:topic_name>".format(v=API_VER), methods=["GET"])
def get_topic_data(topic_name):
    """
    GET /api/<version>/topic_data/<topic_name>

    Get a single data point from a topic over HTTP.
    """
    topic_name = "/" + topic_name
    try:
        msg_class, real_topic, _ = rostopic.get_topic_class(topic_name)
    except rostopic.ROSTopicIOException as e:
        raise e
    if not real_topic:
        return error("Topic does not exist", 404)
    msg = rospy.wait_for_message(real_topic, msg_class)
    data = getattr(msg, "data", None)
    if data is None:
        json = '{"status": ['
        for x in msg.status:
            if x == msg.status[-1]:
                json += '{"name": \"%s\", "level": %d, "message": \"%s\", "hardware_id": \"%s\", "values": %s}]}' % \
                        (x.name if x.name else "null", x.level, \
                         x.message if x.message else "null", x.hardware_id if x.hardware_id else "null", \
                         x.values)
            else:
                json += '{"name": \"%s\", "level": %d, "message": \"%s\", "hardware_id": \"%s\", "values": %s},' % \
                        (x.name if x.name else "null", x.level, \
                         x.message if x.message else "null", x.hardware_id if x.hardware_id else "null", \
                         x.values)
        return Response(json, mimetype = 'application/json')
    else:
	return jsonify({"result": data})

@app.route("/api/{v}/node".format(v=API_VER), methods=["GET"])
def list_nodes():
    """
    GET /api/<version>/node

    List all active ROS nodes
    """
    state = rosnode_master.getSystemState()
    nodes = []
    for s in state:
        for t, l in s:
            nodes.extend(l)
    return jsonify({"results": list(set(nodes))})

@app.route("/api/{v}/node/<path:node_name>".format(v=API_VER), methods=["GET"])
def get_node_info(node_name):
    """
    GET /api/<version>/node/<node_name>

    Get information about a ROS node
    """
    node_name = "/" + node_name
    state = rosnode_master.getSystemState()
    pubs = [t for t, l in state[0] if node_name in l]
    subs = [t for t, l in state[1] if node_name in l]
    srvs = [t for t, l in state[2] if node_name in l]
    return jsonify({
        "node_name": node_name,
        "pubs": pubs,
        "subs": subs,
        "srvs": srvs
    })

if __name__ == '__main__':
    rospy.init_node("api")
    server = WSGIServer(('', 5000), app)
    try:
        rospy.loginfo("API now listening on http://0.0.0.0:5000")
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
