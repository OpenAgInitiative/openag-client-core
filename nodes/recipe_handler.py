#!/usr/bin/python
"""
The `recipe_handler.py` module is in charge of running recipes. It provides a
service `/<environment_id>/start_recipe` which takes as input a recipe ID and
starts the recipe. It also provides a service `/<environment_id>/stop_recipe`
which takes no inputs and stops the currently running recipe. It defines a
parameter `current_recipe` which stores the ID of the currently running recipe.
It also defines a parameter `current_recipe_start` which stores the UNIX
timestamp at which the currently running recipe was started. If no recipe is
running, `current_recipe` will be set to an empty string and
`current_recipe_start` will be set to 0. There should always be exactly one
instance of this module per environment in the system.
"""
import rospy
from roslib.message import get_message_class
from openag.db_names import ENVIRONMENTAL_DATA_POINT, RECIPE
from openag_brain.constants import NULL_SETPOINT_SENTINEL
from openag.cli.config import config as cli_config
from openag.models import EnvironmentalDataPoint
from couchdb import Server
from threading import RLock
from openag_brain import params, services
from openag_brain.srv import StartRecipe, Empty
from openag_brain.load_env_var_types import VariableInfo
from openag_brain.utils import gen_doc_id, read_environment_from_ns
from std_msgs.msg import String, Float64, Bool 
import pdb

# Create a tuple constant of valid environmental variables
# Should these be only environment_variables?
ENVIRONMENTAL_VARIABLES = frozenset(
    VariableInfo.from_dict(d)
    for d in rospy.get_param("/var_types/environment_variables").itervalues())

RECIPE_VARIABLES = frozenset(
    VariableInfo.from_dict(d)
    for d in rospy.get_param("/var_types/recipe_variables").itervalues())

VALID_VARIABLES = ENVIRONMENTAL_VARIABLES.union(RECIPE_VARIABLES)

RECIPE_START = VariableInfo.from_dict(
    rospy.get_param('/var_types/recipe_variables/recipe_start'))

RECIPE_END = VariableInfo.from_dict(
    rospy.get_param('/var_types/recipe_variables/recipe_end'))


# This builds a dictionary of publisher instances using a
# "dictionary comprehension" (syntactic sugar for building dictionaries).
# The constant has to be declared here because get_message_class
# needs to be called after the node is initialized.
PUBLISHERS = {
    variable.name: rospy.Publisher(
        "{}/desired".format(variable.name),
        get_message_class(variable.type),
        queue_size=10)
    for variable in VALID_VARIABLES
}

# A threshold to compare time values in seconds.
THRESHOLD = 1

# Turn on logic tracing by making the variable below True.  
# Output ONLY is written to this node's log file:
# tail -f ~/.ros/log/latest/environments-environment_1-recipe_handler_1-6.log
TRACE = False
def trace(msg, *args):
    if TRACE:
        msg = '\nTRACE> ' + msg
        rospy.logdebug(msg, *args)


#------------------------------------------------------------------------------
# Returns the current 'state', an unordered dictionary of the current value
# of each variable at now_time.
def interpret_simple_recipe(recipe, start_time, now_time):
    """
    Produces a tuple of ``(variable, value)`` pairs by building up
    a recipe state from walking through the recipe keyframes
    """
    _id = recipe["_id"]
    operations = recipe["operations"]
    #trace("recipe_handler: operations: %s", operations)
    end_time_relative = operations[-1][0]
    trace("recipe_handler: interpret_simple_recipe end_time_relative=%s", 
        end_time_relative)
    end_time = start_time + end_time_relative
    # If start time is at some point in the future beyond the threshold
    if start_time - now_time > THRESHOLD:
        raise ValueError("Recipes cannot be scheduled for the future")
    # If there are no recipe operations, immediately start and stop
    # The recipe.
    if not len(operations):
        return (
            (RECIPE_START.name, _id),
            (RECIPE_END.name, _id),
        )
    if now_time >= (end_time + THRESHOLD):
        return ((RECIPE_END.name, _id),)
    if abs(now_time - start_time) < THRESHOLD:
        return ((RECIPE_START.name, _id),)

    now_relative = (now_time - start_time)

    # Create a state object to accrue recipe setpoint values.
    state = {}
    # Build up state up until now_time (inclusive).
    trace("recipe_handler: interpret_simple_recipe now=%s", now_relative)
    for timestamp, variable, value in operations:
        if timestamp > now_relative:
            break
        state[variable] = value
        trace("recipe_handler: interpret_simple_recipe: %s %s %s", 
            timestamp, variable, value)
    trace("recipe_handler: state: %s", state)
    return tuple(
        (variable, value)
        for variable, value in state.iteritems()
    )


RECIPE_INTERPRETERS = {
    "simple": interpret_simple_recipe
}


#------------------------------------------------------------------------------
class RecipeRunningError(Exception):
    """Thrown when trying to set a recipe, but recipe is already running."""
    pass


#------------------------------------------------------------------------------
class RecipeIdleError(Exception):
    """Thrown when trying to clear a recipe, but recipe is already clear."""
    pass


#------------------------------------------------------------------------------
# Our 'babysitting' class that keeps state for the module.
class RecipeHandler:
    """
    RecipeHandler is a manger for keeping track of the currently running recipe
    (if any). It offers threadsafe methods for:

    - getting the currently running recipe
    - setting the recipe
    - clearing the recipe

    and other things. It also contains handlers for the start_recipe
    and stop_recipe services.
    """
    def __init__(self, server, environment):
        # We create a lock to ensure threadsafety, since service handlers are
        # run in a separate thread by ROS.
        self.lock = RLock()
        self.env_data_db = server[ENVIRONMENTAL_DATA_POINT]
        self.recipe_db = server[RECIPE]
        self.environment = environment
        self.__start_time = None
        self.__recipe = None

    def get_recipe(self):
        with self.lock:
            return self.__recipe

    def get_state(self):
        """
        Get the state-related variables of the currently running recipe
        """
        now_time = rospy.get_time()
        start_time = self.__start_time or now_time
        return self.get_recipe(), start_time, now_time

    def set_recipe(self, recipe, start_time):
        """
        Set the currently running recipe... this is the CouchDB recipe document.
        """
        with self.lock:
            if self.__recipe is not None:
                raise RecipeRunningError("Recipe is already running")
            # Set recipe and time
            self.__recipe = recipe
            self.__start_time = start_time
            if self.__start_time is None:
                self.__start_time = rospy.get_time()
            rospy.set_param(params.CURRENT_RECIPE, recipe["_id"])
            rospy.set_param(params.CURRENT_RECIPE_START, self.__start_time  )
        return self

    def clear_recipe(self):
        with self.lock:
            if self.__recipe is None:
                raise RecipeIdleError("No recipe is running")
            # Clear recipe and time
            rospy.set_param(params.CURRENT_RECIPE, "")
            rospy.set_param(params.CURRENT_RECIPE_START, 0)
            self.__recipe = None
            self.__start_time = None
        return self

    def start_recipe_service(self, data, start_time=None):
        recipe_id = data.recipe_id
        if not recipe_id:
            return False, "No recipe id was specified"

        try:
            # Get the recipe document
            recipe = self.recipe_db[recipe_id]
        except Exception as e:
            return False, "\"{}\" does not reference a valid "\
            "recipe".format(recipe_id)

        #trace("recipe_handler: PUBLISHERS=%s", PUBLISHERS)
        trace("recipe_handler: recipe=%s", recipe)

        try:
            # Set the recipe document
            self.set_recipe(recipe, start_time)
        except RecipeRunningError:
            return (
                False,
                "There is already a recipe running. Please stop it "
                "before attempting to start a new one"
            )
        return True, "Success"

    def stop_recipe_service(self, data):
        """Stop recipe ROS service"""
        try:
            self.clear_recipe()
        except RecipeIdleError:
            return False, "There is no recipe running"
        return True, "Success"

    def register_services(self):
        """Register services for instance"""
        rospy.Service(services.START_RECIPE, StartRecipe, 
            self.start_recipe_service)
        rospy.Service(services.STOP_RECIPE, Empty, self.stop_recipe_service)
        rospy.set_param(
            params.SUPPORTED_RECIPE_FORMATS,
            ','.join(RECIPE_INTERPRETERS.keys())
        )
        return self

    def recover_any_previous_recipe(self):
        """
        Attempt to resume any previous recipe that was started but
        not completed.
        """
        # Get the recipe that has been started most recently
        start_view = self.env_data_db.view(
            "openag/by_variable",
            startkey=[self.environment, "desired", RECIPE_START.name],
            endkey=[self.environment, "desired", RECIPE_START.name, {}],
            group_level=3
        )
        if len(start_view) == 0:
            trace("recover_any_previous_recipe: No previous recipe to recover.")
            return
        start_doc = start_view.rows[0].value
        trace("recover_any_previous_recipe: start_doc=%s", start_doc)
        # If a recipe has been ended more recently than the most recent time a
        # recipe was started, don't run the recipe
        end_view = self.env_data_db.view(
            "openag/by_variable",
            startkey=[self.environment, "desired", RECIPE_END.name],
            endkey=[self.environment, "desired", RECIPE_END.name, {}],
            group_level=3
        )
        if len(end_view):
            end_doc = end_view.rows[0].value
            trace("recover_any_previous_recipe: end_doc=%s", end_doc)
            if (end_doc["timestamp"] > start_doc["timestamp"]):
                trace("recover_any_previous_recipe: RETURNING: '\
                    'end_time=%s > start_time=%s", 
                    end_doc["timestamp"], start_doc["timestamp"])
                return
        # Run the recipe
        trace("recover_any_previous_recipe: restarting recipe=%s at time=%s", 
            start_doc["value"], start_doc["timestamp"])
        self.start_recipe_service(
            StartRecipe._request_class(start_doc["value"]),
            start_doc["timestamp"]
        )
        
    def save_recipe_dp(self, variable):
        """
        Save the recipe start/end to the env. data pt. DB, so we can restart
        the recipe if necessary.
        """
        doc = EnvironmentalDataPoint({
            "environment": self.environment,
            "variable": variable,
            "is_desired": True,
            "value": rospy.get_param(params.CURRENT_RECIPE), 
            "timestamp": rospy.get_time()
        })
        doc_id = gen_doc_id(rospy.get_time())
        self.env_data_db[doc_id] = doc
    

#------------------------------------------------------------------------------
# Our ROS node main entry point.  Starts up the node and then waits forever.
if __name__ == '__main__':
    if TRACE:
        rospy.init_node("recipe_handler", log_level=rospy.DEBUG)
    else:
        rospy.init_node("recipe_handler")
    db_server = cli_config["local_server"]["url"]
    if not db_server:
        raise RuntimeError("No local database specified")
    server = Server(db_server)

    namespace = rospy.get_namespace()
    environment = read_environment_from_ns(namespace)

    recipe_handler = RecipeHandler(server, environment)
    recipe_handler.register_services()
    recipe_handler.recover_any_previous_recipe()

    # Subscribe to our own 'recipe_end' message so we can stop publishing
    # and clear the recipe when we get it.
    topic_name = "{}/desired".format(RECIPE_END.name)
    def callback(data):
        recipe_handler.clear_recipe()
        trace("recipe_handler.Subscriber: clearing current recipe.")
    sub = rospy.Subscriber(topic_name, String, callback)

    rate_hz = rospy.get_param('~rate_hz', 1)
    rate = rospy.Rate(rate_hz)
    while not rospy.is_shutdown():
        # Get current recipe state
        recipe_doc, start_time, now_time = recipe_handler.get_state()
        # If we have a recipe, process it. Running a recipe is a blocking
        # operation, so the recipe will stay in this turn of the loop
        # until it is finished.
        if recipe_doc:
            try:
                interpret_recipe = RECIPE_INTERPRETERS[recipe_doc["format"]]
            except KeyError:
                recipe_handler.clear_recipe()
                rospy.logwarn("Invalid recipe format: '%s'",
                    recipe_doc.get("format"))
                continue

            # Get recipe state and publish it
            setpoints = interpret_recipe(recipe_doc, start_time, now_time)
            for variable, value in setpoints:
                try:
                    pub = PUBLISHERS[variable]
                except KeyError:
                    msg = 'Recipe references invalid variable "{}"'
                    rospy.logwarn(msg.format(variable))
                    continue

                # Publish any setpoints that we can
                trace("recipe_handler publish: %s, %s", variable, value)
                if variable == RECIPE_END.name:
                    trace("recipe_handler publish: END!")
                    # Write an env. data pt. for when we stopped this recipe.
                    recipe_handler.save_recipe_dp(variable)
                elif variable == RECIPE_START.name:
                    # Write an env. data pt. for when we started this recipe.
                    recipe_handler.save_recipe_dp(variable)
                try:
                    pub.publish(value)
                except ValueError:
                    pass

        rate.sleep()
        # end of while loop in main



