#!/usr/bin/env python
"""
Python implementation of an on-off controller, also known as bang-bang or
hysteresis controller.

Parameters:
- inverted_output[Bool]: If the current state is above the setpoint, the
  output should have a True value. Used to control actuators like a cooler.
- hysteresis_width[Float]: Region where the previous output is kept even if the
  setpoint has been passed, used to avoid high-frequency oscillations.
"""

from controllers import ClosedLoopController
from std_msgs.msg import Bool

class OnOff(ClosedLoopController):
    output_type = Bool

    def __init__(self, inverted_output=False, hysteresis_width=0):
        self.inverted_output = inverted_output
        self.hysteresis_width = hysteresis_width
        self.last_output = None

    def update(self, state):
        if self.set_point is None:
            return

        error = self.set_point - state
        in_hysteresis = abs(error) < self.hysteresis_width
        if in_hysteresis and self.last_output is not None:
            # Error magnitude is within the hysteresis_width,
            # keep sending the previous output.
            return self.last_output

        if self.inverted_output:
            # Measured state is above the set_point, turn output ON
            # e.g. Cooler
            output = state > self.set_point
        else:
            # Measured state is below the set_point, turn output ON
            # e.g. Heater, Water leveler
            output = state < self.set_point

        self.last_output = output
        return output

if __name__ == '__main__':
    OnOff.start()
