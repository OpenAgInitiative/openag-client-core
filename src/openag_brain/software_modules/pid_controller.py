#!/usr/bin/env python
"""
The `controller.py` module is a Python implementation of a
Proportional-Integral-Derivative controller for ROS.It also reads configuration from a number of other ROS parameters as well. The
controller gains are passed in as parameters `Kp`, `Ki`, and `Kd`. It also
accepts an `upper_limit` and `lower_limit` to bound the control effort output.
`windup_limit` defines a limit for the integrator of the control loop.
`deadband_width` can be used to apply a deadband to the control efforts.
Specifically, commands with absolute value less than `deadband_width` will be
changed to 0.
"""
from controllers import ClosedLoopController

class PID(ClosedLoopController):
    """ Discrete PID control """

    def __init__(self, Kp=0, Ki=0, Kd=0, upper_limit=1, lower_limit=-1,
            windup_limit=1000, deadband_width=0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.windup_limit = windup_limit
        self.deadband_width = deadband_width

        self.last_error = 0
        self.integrator = 0

    def update(self, state):
        if self.set_point is None:
            return

        error = self.set_point - state

        if abs(error) < self.deadband_width:
            return 0

        p_value = self.Kp * error
        d_value = self.Kd * (error - self.last_error)
        self.last_error = error
        self.integrator = self.integrator + error
        self.integrator = max(-self.windup_limit, min(self.windup_limit, self.integrator))
        i_value = self.Ki * self.integrator

        res = p_value + i_value + d_value
        res = min(self.upper_limit, max(self.lower_limit, res))

        return res

if __name__ == '__main__':
    PID.start()
