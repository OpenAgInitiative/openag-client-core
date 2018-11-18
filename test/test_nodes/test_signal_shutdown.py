#!/usr/bin/env python
PKG = 'openag_brain'
NAME = 'test_signal_shutdown'

import sys
import unittest
import rospy
from std_msgs.msg import Float64

from nodes.signal_shutdown import setup_gpio_pins, check_for_shutdown

class TestSignalShutdown(unittest.TestCase):
    """
    Test the signal shutdown module to see if it starts up without errors
    """

    def test_setup(self):
        setup_gpio_pins()

    def test_signal_shutdown(self):
        setup_gpio_pins()
        check_for_shutdown()

if __name__ == "__main__":
    import rostest
    rostest.rosrun(PKG, NAME, TestSignalShutdown)
