#!/usr/bin/env python
"""
`sensor_am2315.py` handles communication with the
`AM2315 temperature and humidity sensor <https://www.adafruit.com/products/1293>`_.
"""
import rospy
from std_msgs.msg import Float64
from openag_brain.peripherals.am2315 import AM2315

if __name__ == '__main__':
    rospy.init_node("sensor_am2315")
    i2c_addr = rospy.get_param("~i2c_addr", 0x5c)
    i2c_bus = rospy.get_param("~i2c_bus", "/dev/i2c-1")
    temp_pub = rospy.Publisher("air_temperature/raw", Float64, queue_size=10)
    humid_pub = rospy.Publisher("air_humidity/raw", Float64, queue_size=10)
    rate = rospy.get_param("~rate_hz", 1)
    r = rospy.Rate(rate)
    with AM2315(i2c_addr, i2c_bus) as am2315:
        while not rospy.is_shutdown():
            am2315.poll()
            if am2315.temperature:
                temp_pub.publish(temp)
            if am2315.humidity:
                humid_pub.publish(humid)
            # Use rate timer instance to sleep until next turn
            r.sleep()
