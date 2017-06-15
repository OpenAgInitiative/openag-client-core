from __future__ import division
import rospy
from openag_brain.load_env_var_types import VariableInfo
from openag_brain.settings import trace
from datetime import datetime

RECIPE_START = VariableInfo.from_dict(
    rospy.get_param('/var_types/recipe_variables/recipe_start'))

RECIPE_END = VariableInfo.from_dict(
    rospy.get_param('/var_types/recipe_variables/recipe_end'))

# A threshold to compare time values in seconds.
THRESHOLD = 1

EPOCH = datetime.utcfromtimestamp(0)
def unix_time_seconds(dt):
     return (dt - EPOCH).total_seconds()

MIN_DATE = unix_time_seconds(datetime.strptime('06-11-2010 07:00:00', '%m-%d-%Y %H:%M:%S')) # For verifying time format
MAX_DATE = unix_time_seconds(datetime.strptime('06-11-2035 07:00:00', '%m-%d-%Y %H:%M:%S'))


def interpret_simple_recipe(recipe, start_time, now_time):
    """
    Produces a tuple of ``(variable, value)`` pairs by building up
    a recipe state from walking through the recipe keyframes
    """
    _id = recipe["_id"]
    operations = recipe["operations"]
    rospy.logdebug(operations)
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
    rospy.logdebug(state)
    return tuple(
        (variable, value)
        for variable, value in state.iteritems()
    )


def interpret_flexformat_recipe(recipe, start_time, now_time):
    """
    Recipe Interpreter should read a recipe, now_time, start_time, variable and return a value.
       Determine the time since the beginning of the recipe.
       Determine what is the current step
       Calculate the remaining time left in this step.
       Look up the value within that step for that variable.
    """
    _id = recipe["_id"]
    rospy.logdebug(recipe["phases"])
    [verify_time_units(_) for _ in (now_time, start_time)]
    # If start time is at some point in the future beyond the threshold
    if start_time - now_time > THRESHOLD:
        raise ValueError("Recipes cannot be scheduled for the future")
    # If there are no recipe operations, immediately start and stop
    # The recipe.
    if not len(recipe['phases']):
        return (
            (RECIPE_START.name, _id),
            (RECIPE_END.name, _id),
        )
    if abs(now_time - start_time) < THRESHOLD:
        return ((RECIPE_START.name, _id),)
    time_units = verify_time_units_are_consistent(recipe['phases'])
    # Returns a list of the phases and step durations  [(duration_of_phase_1, duration_of_step_1), (duration_of_phase_2, duration_of_step_2), etc]
    duration_of_phases_steps = calc_duration_of_phases_steps(recipe['phases'])
    current_phase_number, duration_in_step = calc_phase_and_time_remaining(duration_of_phases_steps,
                                                                           start_time,
                                                                           now_time,
                                                                           time_units)
    # Need to create a function to calculate the end time of the recipe
    #if now_time >= (end_time + THRESHOLD):
    #    return ((RECIPE_END.name, _id),)
    current_phase = recipe['phases'][current_phase_number]
    state = {}
    for variable, variable_step_data in current_phase['step'].items():
        value = determine_value_for_step(variable_step_data, duration_in_step)
        state[variable] = value
    return tuple(
        (variable, value)
        for variable, value in state.iteritems()
    )


def verify_time_units(time_var):
    """
    Verifies the units for incoming time variables are valid.
    """
    if not MIN_DATE < time_var < MAX_DATE:
        raise TypeError("Variable time format is not correct. The value should be between {} and {}, but received: ".format(MIN_DATE, MAX_DATE, time_var))


def verify_time_units_are_consistent(recipe_phases):
    """
    The time units are stored for each phase in the recipe rather than at the recipe level. Need to verify they all match for now.
    Later add ability for them to be different.
    """
    time_units = None
    for phase in recipe_phases:
        if 'time_units' not in phase:
            raise KeyError("time_units is missing from the phase. Please check recipe format")
        if not time_units:
            time_units = phase['time_units']
        elif time_units != phase['time_units']:
            raise Exception("time_units are not consistent across each phase in the recipe. {} != {}".format(time_units, phase['time_units']))
    return time_units

def determine_value_for_step(variable_step_data, duration_in_step):
    """
    variable_step_data = [{"start_time": 0, "end_time": 6, "value": 20},
                          {"start_time": 6, "end_time": 18, "value": 23},
                          {"start_time": 18, "end_time": 24, "value": 19}]
    duration_in_step = 15
    Given the time within a step, what value is expected.
    """

    for row in variable_step_data:
        if row['start_time'] <= duration_in_step <= row['end_time']:
            return row['value']


def calculate_max_duration_from_step(step):
    """
    Determines the total duration of this step. Normally it is 24 hours.
       Could add other validation steps here as well.
       Convert to numpy and use argmax
    """
    max_time = 0
    for variable, start_end_times in step.items():
        for data in start_end_times:
            if data['start_time'] > data['end_time']:
                raise Exception("Start_time is after end time.")
            elif max_time < max(data['start_time'], data['end_time']):
                max_time = max(data['start_time'], data['end_time'])
    return max_time


def calc_duration_of_phases_steps(phases):
    """
    Returns a list with the duration of the step and the entire phase
    """
    duration_of_phases_steps = []
    for phase in phases:
        cycles = phase['cycles']
        max_duration = calculate_max_duration_from_step(phase['step'])
        duration_of_phases_steps.append((cycles*max_duration, max_duration))
    return duration_of_phases_steps


def convert_duration_units(duration, units='hours'):
    """
    Converts a number duration from Seconds into the units specified in the options(units variable).
    """
    divider = {'hours': 3600,
                  'days': 3600*24,
                  'milliseconds': 0.001,
                  'ms': 0.001,
                  'seconds': 1
                }
    if units not in divider:
        raise KeyError("Error time_units in recipe are not available. Valid options are: days, hours, milliseconds, ms")
    return duration / divider[units]


def offset_duration_by_time_from_start(start_time):
    """
    Calculates how many hours are used in the current day, so the times set in the recipe are relative to midnight, not start_time

    """
    #raise NotImplementedError("Function not implemented yet.")
    start_time_dt_format = datetime.utcfromtimestamp(start_time)
    return start_time_dt_format.hour * 3600

def calc_phase_and_time_remaining(duration_of_phases_steps, start_time, now_time, time_units):
    """
    Calculates how far along the recipe is in progress given the start_time and the time it is now (aka now_time).
    TODO: Add function to determine the starting point: Subtract the hours out of the current day from the elapsed time.

    duration_of_phases_steps == [(336, 24), (480, 24), (168, 24)]  #total Hours in phase, hours per step in phase (usually days)
    now_time : datetime : Local current time in seconds from EPOCH
    start_time : datetime : Local time the recipe started in seconds from EPOCH
    return: current_phase_number, duration_in_phase

    """
    time_elapsed = now_time - start_time
    #time_elapsed = time_elapsed - offset_duration_by_time_from_start(start_time)  # Offset elapsed time by hours on first day. this method doesn't work.
    time_elapsed = convert_duration_units(time_elapsed, time_units)
    for i, (total_duration, step_duration) in enumerate(duration_of_phases_steps):
        if time_elapsed > total_duration:
            time_elapsed -= total_duration
        else:
            duration_in_phase = time_elapsed % step_duration
            current_phase_number = i
            break
    return current_phase_number, duration_in_phase
