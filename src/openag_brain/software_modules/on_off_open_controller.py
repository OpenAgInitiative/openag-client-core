#!/usr/bin/env python
"""
Python implementation of an on-off open-loop controller,
also known as bang-bang or hysteresis controller.

Parameters:
 - threshold[Float]: Value to compare the set point against.
 - below_threshold[Bool]: If the set point is above the value, the output
    should have a True value (ON). Used to control actuators like a cooler.
"""

from controllers import OpenLoopController
from std_msgs.msg import Bool

class OnOffOpen(OpenLoopController):
    output_type = Bool

    def __init__(self, threshold=0, activate_below_threshold=False):
        self.threshold = threshold
        self.activate_below_threshold = activate_below_threshold

    def update(self, set_point):
        if self.activate_below_threshold:
            # Set point is below the threshold, turn output ON
            # e.g. Cooler
            output = set_point < self.threshold
        else:
            # Set point is above the threshold, turn output ON
            # e.g. Heater, Water leveler
            output = set_point > self.threshold

        return output

if __name__ == '__main__':
    OnOffOpen.start()
