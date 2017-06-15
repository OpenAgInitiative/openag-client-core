#!/usr/bin/env python
PKG="openag_brain"

import sys, os
import unittest, pytest
from time import time
from datetime import datetime
import json

from openag_brain.recipe_interpreters import *
DIR_NAME = os.path.dirname(__file__)
sys.path.append(os.path.join(DIR_NAME, '../..'))
from data.mock_recipes import MOCK_RECIPE_SIMPLE_A, MOCK_RECIPE_FLEXFORMAT_A


def load_recipe_from_file(file_name):
    with open(file_name, 'r') as f:
        recipe = json.load(f)
    return recipe


def _test_load_recipe_from_file():
    recipe = load_recipe_from_file(os.path.join(DIR_NAME, '../../test/data/mock_recipe_v3.json'))
    print(recipe)
    assert type(recipe) == dict
    assert False


EPOCH = datetime.utcfromtimestamp(0)

def unix_time_seconds(dt):
    return (dt - EPOCH).total_seconds()

def test_check_timezone_conversions():
    c = datetime.now()
    assert datetime.utcfromtimestamp(unix_time_seconds(c)) == c

class TestRecipeInterpreterSimple(unittest.TestCase):

    def test_interpret_simple_recipe(self):
        now_time = time()
        start_time = now_time - 10
        setpoints = interpret_simple_recipe(MOCK_RECIPE_SIMPLE_A, start_time, now_time)
        assert len(setpoints) == 2


class TestRecipeInterpreterFlexFormat(unittest.TestCase):

    def test_interpret_flexformat_recipe(self):
        #now_time = time()
        #start_time = now_time - 10
        start_time = unix_time_seconds(datetime.strptime("2017-04-17 14:00", "%Y-%m-%d %H:%S"))
        now_time = unix_time_seconds(datetime.strptime("2017-04-18 20:00", "%Y-%m-%d %H:%S"))
        setpoints = interpret_flexformat_recipe(MOCK_RECIPE_FLEXFORMAT_A, start_time, now_time)
        assert len(setpoints) == 5

        start_time = 1497025128.31   
        now_time = 1497025129.32
        setpoints = interpret_flexformat_recipe(MOCK_RECIPE_FLEXFORMAT_A, start_time, now_time)
        rospy.loginfo(setpoints)
        setpoints_dict = dict(setpoints)
        assert setpoints_dict['light_intensity_red'] == 1
        assert setpoints_dict['air_temperature'] == 22
        assert len(setpoints) == 5

    def test_verify_time_units(self):
        """
        Tests Verifies the start_time and now_time variables are in the correct format.
        """
        date1 = datetime.strptime('06-11-2017 07:00:00', '%m-%d-%Y %H:%M:%S')
        dates_to_verify = [(date1, False),
                           (unix_time_seconds(date1), True),
                           (unix_time_seconds(date1)*1000, False),
                           ('06-11-2017 07:00:00', False)]
        for date_var, valid_type in dates_to_verify:
            if valid_type:
                assert verify_time_units(date_var) == None
            else:
                with pytest.raises(TypeError):
                    verify_time_units(date_var)
        

    def test_offset_duration_by_time_from_start(self):
        start_times = [(unix_time_seconds(datetime.strptime("2017-04-17 14:00", "%Y-%m-%d %H:%S")), 14*3600),
                       (unix_time_seconds(datetime.strptime("2017-04-17 4:00", "%Y-%m-%d %H:%S")), 4*3600),
                       (unix_time_seconds(datetime.strptime("2017-04-17 10:00", "%Y-%m-%d %H:%S")), 10*3600),
                       (unix_time_seconds(datetime.strptime("2017-04-17 23:00", "%Y-%m-%d %H:%S")), 23*3600)]
        for start_time, offset in start_times:
            assert offset_duration_by_time_from_start(start_time) == offset


    def test_calc_phase_and_time_remaining(self):
        duration_of_phases_steps = [(336, 24), (480, 24), (168, 24)]
        start_time = unix_time_seconds(datetime.strptime("2017-04-17 14:00", "%Y-%m-%d %H:%S"))
        current_time = unix_time_seconds(datetime.strptime("2017-04-18 20:00", "%Y-%m-%d %H:%S"))
        current_phase_number, duration_in_step = calc_phase_and_time_remaining(duration_of_phases_steps,
                                               current_time, start_time, 'hours')
        #assert (current_phase_number, duration_in_step) == (0, 20)   # Need to fix how the current phase is calculated given the start_time
        assert (current_phase_number, duration_in_step) == (0, 18)

        start_time = unix_time_seconds(datetime.strptime("2017-04-17 14:00", "%Y-%m-%d %H:%S"))
        current_time = unix_time_seconds(datetime.strptime("2017-04-18 03:00", "%Y-%m-%d %H:%S"))
        current_phase_number, duration_in_step = calc_phase_and_time_remaining(duration_of_phases_steps,
                                               current_time, start_time, 'hours')
        print(current_phase_number, duration_in_step)
        #assert (current_phase_number, duration_in_step) == (0, 3)
        assert (current_phase_number, duration_in_step) == (0, 11)


    def test_convert_duration_units(self):
                             
        time_conversions = [(3600, 'hours', 1),   #in milliseconds   == 1 hour
                            (3600, 'seconds', 3600), 
                            (3600, 'ms', 3600000), 
                            (3600, 'days', 0.0416666)
                           ]
        for time_since_start, time_units, expected_duration in time_conversions:
            actual_duration = convert_duration_units(time_since_start, time_units)
            assert round(expected_duration, 4) == round(actual_duration, 4)


    def test_calculate_max_duration_from_step(self):
        step = { "air_temperature": [{"start_time": 0, "end_time": 6, "value": 20},
                                      {"start_time": 6, "end_time": 18, "value": 23},
                                      {"start_time": 18, "end_time": 24, "value": 19}],
                  "nutrient_flora_duo_a": [{"start_time": 0, "end_time": 6, "value": 5},
                                           {"start_time": 6, "end_time": 18, "value": 2},
                                           {"start_time": 18, "end_time": 24, "value": 5}],
                  "nutrient_flora_duo_b": [{"start_time": 0, "end_time": 6, "value": 2}],
                  "light_illuminance": [{"start_time": 0, "end_time": 6, "value": 4},
                                        {"start_time": 18, "end_time": 24, "value": 3}],
            }
        max_time = calculate_max_duration_from_step(step)
        assert max_time == 24


    def test_calc_duration_of_phases_steps(self):
        phases = [    # Previously operations,  Needs to be an ordered dictionary.
              { "name": "early",
                "cycles": 14,    # Add check for duration of a step to be a total of 24 hours. (Not a necessarity but valuable for consistency/simplicity)
                "step": { "air_temperature": [{"start_time": 0, "end_time": 6, "value": 20},
                                              {"start_time": 6, "end_time": 18, "value": 23},
                                              {"start_time": 18, "end_time": 24, "value": 19}],
                          "nutrient_flora_duo_a": [{"start_time": 0, "end_time": 6, "value": 5},
                                                   {"start_time": 6, "end_time": 18, "value": 2},
                                                   {"start_time": 18, "end_time": 24, "value": 5}],
                          "nutrient_flora_duo_b": [{"start_time": 0, "end_time": 6, "value": 2}],
                          "light_illuminance": [{"start_time": 0, "end_time": 6, "value": 4},
                                                {"start_time": 18, "end_time": 24, "value": 3}],
                    },
              },
              { "name": "middle",
                "cycles": 20,
                "step": { "air_temperature": [{"start_time": 0, "end_time": 6, "value": 20},
                                              {"start_time": 6, "end_time": 18, "value": 23},
                                              {"start_time": 18, "end_time": 24, "value": 19}],
                          "nutrient_flora_duo_a": [{"start_time": 6, "end_time": 18, "value": 1.4}],
                          "nutrient_flora_duo_b": [{"start_time": 6, "end_time": 18, "value": 0.7}],
                          "light_illuminance": [{"start_time": 6, "end_time": 18, "value": 1}],
                    },
              },
              { "name": "late",
                "cycles": 7,
                "step": { "air_temperature": [{"start_time": 6, "end_time": 24, "value": 23}],
                        },
              }
            ]
        duration_of_phases_steps = calc_duration_of_phases_steps(phases)
        assert duration_of_phases_steps == [(336, 24), (480, 24), (168, 24)]


    def test_determine_value_for_step(self):
        variable_step_data = [{"start_time": 0, "end_time": 6, "value": 20},
                              {"start_time": 6, "end_time": 18, "value": 23},
                              {"start_time": 18, "end_time": 24, "value": 19}]
        duration_in_step = 15
        value = determine_value_for_step(variable_step_data, duration_in_step)
        assert value == 23
        duration_in_step = 0
        value = determine_value_for_step(variable_step_data, duration_in_step)
        assert value == 20

    def test_verify_time_units_are_consistent(self):
        time_units = verify_time_units_are_consistent(MOCK_RECIPE_FLEXFORMAT_A['phases'])
        assert time_units == 'hours'


if __name__ == '__main__':
   import rosunit
   rosunit.unitrun(PKG, 'test_recipe_interpreter', TestRecipeInterpreter)
