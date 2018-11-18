#!/usr/bin/env python
# Simple script for shutting down the raspberry Pi at the press of a button.
# by Inderpreet Singh
# Adapted by Jake Rye and Bob Davis

import RPi.GPIO as GPIO
import time
import os
import logging
import rospy
from std_msgs.msg import Float64

# This is needed to account for any erroraneous drops in the shutdown signal
VERIFICATION_TIME_SEC = 3          # Time to wait to verify shutdown signal
SHUTDOWN_SIGNAL_THRESHOLD = 0.98   # Percent of shutdown signals needed to
                                   # signal a shutdown (ranges from 0 to 1)


def setup_gpio_pins():
    # Use the Broadcom SOC Pin numbers
    # Setup the Pin with Internal pullups enabled and PIN in reading mode.
    rospy.logdebug('Setting GPIO27 / PIN13 to INPUT PULLUP')
    GPIO.setmode(GPIO.BOARD)
    # PIN13 / BCM 27 YELLOW / SW-COM - Signals Shutdown
    GPIO.setup(13, GPIO.IN, pull_up_down = GPIO.PUD_UP)

    # Turn delay relay on
    # Sends signal to the relay to stay on until this drops low.
    rospy.logdebug('Setting GPIO22 / PIN15 to OUTPUT HIGH')
    GPIO.setup(15, GPIO.OUT) # PIN15 / BCM 22 / WHITE / CH1
    GPIO.output(15, GPIO.HIGH)


def check_for_shutdown():
    # Monitor pin for stable signal to safely shutdown
    while not rospy.is_shutdown():
        rospy.logdebug("GPIO13: {}".format(GPIO.input(13)))
        if not GPIO.input(13):
            rospy.logdebug('Initiating safe shutdown sequence')
            successful_debounce = True
            input_sum = 0
            for i in range(VERIFICATION_TIME_SEC * 1000):
                input_sum += GPIO.input(13)
                time.sleep(0.001)
            avg_signal = input_sum / ( VERIFICATION_TIME_SEC * 1000)
            rospy.logdebug('The average signal after {} seconds was {}'.format(
                           VERIFICATION_TIME_SEC, avg_signal))
            if avg_signal > (1 - SHUTDOWN_SIGNAL_THRESHOLD):  # avg_signal should be 0 for 100% valid
                rospy.logwarn('Signal interrupted, breaking out of safe shutdown sequence')
                successful_debounce = False
                continue

            if successful_debounce:
                rospy.logdebug('Safely shutting down')
                rospy.signal_shutdown('Safely shutting down due to Power Off Button')
                time.sleep(5)
                GPIO.output(15, GPIO.LOW)
                os.system("sudo shutdown -h now")
                break
        rospy.sleep(1.)


if __name__ == '__main__':
    rospy.init_node('signal_shutdown')
    setup_gpio_pins()
    try:
        check_for_shutdown()
    except rospy.ROSInterruptException:
        pass
