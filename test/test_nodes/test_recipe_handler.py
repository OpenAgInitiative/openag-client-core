#!/usr/bin/env python

# Run the tests like this:
# cd ~/catkin_ws
# rostest openag_brain test_recipe_handler.launch

PKG = 'openag_brain'
NAME = 'test_recipe_handler'

import sys, os
import unittest
from time import time
import rospy
from std_msgs.msg import Float64
from openag_brain import services
from openag_brain.srv import StartRecipe

# Hack to allow importing of functions from ros nodes. 
#  Ideas to come up with a permanent solution: (Need to research the best known
#  methods) 
#     1. Figure out how nodes are loaded into the default path or if they
#        are just run as subprocesses by ros
#     2. Split out functions as a separate services or move to a standard
#        library to be imported into the nodes.  This would mean the nodes do
#        nothing but run services, publish and script to topics.
DIR_NAME = os.path.dirname(__file__)
sys.path.append(os.path.join(DIR_NAME, '../..'))
from nodes.recipe_handler import interpret_simple_recipe


MOCK_RECIPE_A = {
  "_id": "air_water_temp_test",
  "format": "simple",
  "version": "0.0.1",
  "operations": [
    [0, "air_temperature", 24],
    [0, "water_temperature", 22],
    [30, "air_temperature", 24],  # Lesson Learned interpret_simple_recipe calculates the end time by the last time in the list
    [30, "water_temperature", 22]
  ]
}

MOCK_RECIPE_B = {
  "_id": "test",
  "version": "6.1.7",
  "format": "simple",
  "operations": [
    # recipe_start
    [ 0, "one", 1 ],
    [ 0, "two", 2 ],
    [ 0, "three", 3 ],
    [ 60, "four", 4 ],
    [ 60, "five", 5 ],
    [ 120, "six", 6 ],
    [ 120, "seven", 7 ],
    [ 180, "eight", 8 ],
    # recipe_end
  ]
}

class TestRecipeHandler(unittest.TestCase):
    """
    Test the recipe_handler.py node to verify it is returning the topics
    correctly.
    """

    def test_recipe_interpreter(self):
        now_time = time()
        # Test for recipe in process
        start_time = now_time - 10
        setpoints = interpret_simple_recipe(MOCK_RECIPE_A, start_time, now_time)
        assert len(setpoints) == 2, 'len(setpoints)=%d' % len(setpoints)
        # Test for completed recipe
        start_time = now_time - 300
        setpoints = interpret_simple_recipe(MOCK_RECIPE_A, start_time, now_time)
        assert setpoints[0][0] == 'recipe_end', 'recipe_end=' % setpoints[0][0]

    #--------------------------------------------------------------------------
    def test_B(self):
        # Test we only get the start, time is at the beginning.
        now_time = time()
        start_time = now_time
        setpoints = interpret_simple_recipe(MOCK_RECIPE_B, start_time, now_time)
        assert len(setpoints) == 1, 'len(setpoints)=%d' % len(setpoints)
        assert setpoints[0][0] == 'recipe_start', \
            'setpoints[0][0]=%s but should be recipe_start' % setpoints[0][0]

        # Test for recipe in process at first change (1 secs in)
        now_time = time()
        start_time = now_time - 1
        setpoints = interpret_simple_recipe(MOCK_RECIPE_B, start_time, now_time)
        # setpoints contains the state tuples at now_time - NOT in order. 
        assert len(setpoints) == 3, \
            'len(setpoints)=%d should be 3' % len(setpoints)
        # setpoints are in RANDON order (but always the same)
        assert setpoints[0][0] == 'three', \
            'setpoints[0][0]=%s but should be three' % setpoints[0][0]
        assert setpoints[1][0] == 'two', \
            'setpoints[1][0]=%s but should be two' % setpoints[1][0]
        assert setpoints[2][0] == 'one', \
            'setpoints[2][0]=%s but should be one' % setpoints[2][0]

        # Test for recipe in process at next change (60 secs in)
        now_time = time()
        start_time = now_time - 60 
        setpoints = interpret_simple_recipe(MOCK_RECIPE_B, start_time, now_time)
        assert len(setpoints) == 5, \
            'len(setpoints)=%d should be 5' % len(setpoints)
        # found the order using this:
        #assert False, '%s, %s, %s, %s, %s' % (setpoints[0][0], setpoints[1][0], setpoints[2][0], setpoints[3][0], setpoints[4][0])
        assert setpoints[0][0] == 'four', \
              'setpoints[0][0]=%s but should be four' % setpoints[0][0]
        assert setpoints[1][0] == 'three', \
              'setpoints[1][0]=%s but should be three' % setpoints[1][0]
        assert setpoints[2][0] == 'five', \
              'setpoints[2][0]=%s but should be five' % setpoints[2][0]
        assert setpoints[3][0] == 'two', \
              'setpoints[3][0]=%s but should be two' % setpoints[3][0]
        assert setpoints[4][0] == 'one', \
              'setpoints[4][0]=%s but should be one' % setpoints[4][0]

        # Test for recipe in process at next change (120 secs in)
        now_time = time()
        start_time = now_time - 120
        setpoints = interpret_simple_recipe(MOCK_RECIPE_B, start_time, now_time)
        assert len(setpoints) == 7, \
            'len(setpoints)=%d should be 7' % len(setpoints)
        #assert False, '%s, %s, %s, %s, %s, %s, %s' % (setpoints[0][0], setpoints[1][0], setpoints[2][0], setpoints[3][0], setpoints[4][0], setpoints[5][0], setpoints[6][0])
        # seven, six, three, two, four, five, one
        assert setpoints[0][0] == 'seven', \
              'setpoints[0][0]=%s but should be seven' % setpoints[0][0]
        assert setpoints[1][0] == 'six', \
              'setpoints[1][0]=%s but should be six' % setpoints[1][0]
        assert setpoints[2][0] == 'three', \
              'setpoints[2][0]=%s but should be three' % setpoints[2][0]
        assert setpoints[3][0] == 'two', \
              'setpoints[3][0]=%s but should be two' % setpoints[3][0]
        assert setpoints[4][0] == 'four', \
              'setpoints[4][0]=%s but should be four' % setpoints[4][0]
        assert setpoints[5][0] == 'five', \
              'setpoints[5][0]=%s but should be five' % setpoints[5][0]
        assert setpoints[6][0] == 'one', \
              'setpoints[6][0]=%s but should be one' % setpoints[6][0]

        # Test for recipe in process at last time change (180 secs in)
        now_time = time()
        start_time = now_time - 180
        setpoints = interpret_simple_recipe(MOCK_RECIPE_B, start_time, now_time)
        assert len(setpoints) == 8, \
            'len(setpoints)=%d should be 8' % len(setpoints)
        #assert False, '%s, %s, %s, %s, %s, %s, %s, %s' % (setpoints[0][0], setpoints[1][0], setpoints[2][0], setpoints[3][0], setpoints[4][0], setpoints[5][0], setpoints[6][0], setpoints[7][0])
        # seven, six, three, two, four, five, eight, one
        assert setpoints[0][0] == 'seven', \
              'setpoints[0][0]=%s but should be seven' % setpoints[0][0]
        assert setpoints[1][0] == 'six', \
              'setpoints[1][0]=%s but should be six' % setpoints[1][0]
        assert setpoints[2][0] == 'three', \
              'setpoints[2][0]=%s but should be three' % setpoints[2][0]
        assert setpoints[3][0] == 'two', \
              'setpoints[3][0]=%s but should be two' % setpoints[3][0]
        assert setpoints[4][0] == 'four', \
              'setpoints[4][0]=%s but should be four' % setpoints[4][0]
        assert setpoints[5][0] == 'five', \
              'setpoints[5][0]=%s but should be five' % setpoints[5][0]
        assert setpoints[6][0] == 'eight', \
              'setpoints[6][0]=%s but should be eight' % setpoints[6][0]
        assert setpoints[7][0] == 'one', \
              'setpoints[7][0]=%s but should be one' % setpoints[7][0]

        # Test for recipe end
        now_time = time()
        start_time = now_time - 181
        setpoints = interpret_simple_recipe(MOCK_RECIPE_B, start_time, now_time)
        assert len(setpoints) == 1, 'len(setpoints)=%d' % len(setpoints)
        assert setpoints[0][0] == 'recipe_end', \
            'setpoints[0][0]=%s' % setpoints[0][0]


    #--------------------------------------------------------------------------
    def test_start_recipe(self):
       rospy.wait_for_service(services.START_RECIPE)
       s = rospy.ServiceProxy(services.START_RECIPE, StartRecipe)


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import rostest
    rostest.rosrun(PKG, NAME, TestRecipeHandler)

