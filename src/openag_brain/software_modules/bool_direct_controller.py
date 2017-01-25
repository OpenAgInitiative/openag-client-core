#!/usr/bin/env python
"""
Python implementation an open-loop controller that just interprets a Bool
setpoint as a direct command to the actuator
"""
from controllers import OpenLoopController
from std_msgs.msg import Bool

class BoolDirect(OpenLoopController):
    output_type = Bool
    def update(self, set_point):
        return set_point

if __name__ == '__main__':
    BoolDirect.start()
