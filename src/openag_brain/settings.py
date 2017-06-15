import rospy

# Turn on logic tracing by making the variable below True.
# Output ONLY is written to this node's log file:
# tail -f ~/.ros/log/latest/environments-environment_1-recipe_handler_1-6.log
TRACE = False
def trace(msg, *args):
    if TRACE:
        msg = '\nTRACE> ' + msg
        rospy.logdebug(msg, *args)
