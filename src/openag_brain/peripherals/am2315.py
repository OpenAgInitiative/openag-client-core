"""
This module consists of code for interacting with the AM2315 temperature and
humidity sensor.
"""

import rospy
import time
from periphery import I2C, I2CError

class AM2315:
    """
    Class that represents a AM2315 temperature and humidity sensor instance
    and provides functions for interfacing with the sensor.

    One instance = 1 successful i2c connection.
    """

    def __init__(self, i2c_addr = 0x5c, i2c_bus = "/dev/i2c-1"):
        self.__i2c_master = None
        self.i2c_addr = i2c_addr
        self.i2c_bus = i2c_bus
        self.temperature = None
        self.humidity = None
        self.regRhMSB = 0x00
        self.regRhLSB = 0x01
        self.regTmpMSB = 0x02
        self.regTmpLSB = 0x03
        self.regModelHi = 0x08
        self.regModelLo = 0x09
        self.regVersion = 0x0a
        self.regIDA = 0x0b
        self.regIDB = 0x0c
        self.regIDD = 0x0d
        self.regIDE = 0x0e
        self.regStat = 0x0f
        self.regUsrAMSB = 0x10
        self.regUsrALSB = 0x11
        self.regUsrBMSB = 0x12
        self.regUsrBLSB = 0x13
        self.cmdReadReg = 0x03
        # Attempt I2C connect.
        self.connect()

    def __del__(self):
        """
        Destructor will close the I2C manager if instance is garbage collected.
        """
        if self.__i2c_master:
            self.__i2c_master.close()

    def __enter__(self):
        """
        We use the __enter__ and exit methods to manage the lifecycle of
        i2c managers. This class can be used with the ``with`` keyword.
        See https://www.python.org/dev/peps/pep-0343/ for more on `with`.

        Example::

            with AM2315() as am2315:
              am2315.poll()
        """
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        # Close the I2C manager on exit.
        if self.__i2c_master:
            self.__i2c_master.close()

    def connect(self):
        # Instantiate the periphery I2C manager. If it fails it will raise
        # an I2CError, which we then catch.
        # If we have an ``__i2c_master`` it means we have a successful
        # connection.
        # See http://python-periphery.readthedocs.io/en/latest/i2c.html
        try:
            self.__i2c_master = I2C(self.i2c_bus)
            rospy.loginfo("Connected to AM2315")
        except I2CError:
            rospy.logwarn("Failed to connect to AM2315")
            pass

    def poll(self):
        if self.__i2c_master:
            try:
                self.temperature, self.humidity = self.get_temp_humid()
            except:
                self.temperature = None
                self.humidity = None
        else:
            self.connect()

    def get_signed(self, unsigned):
        """
        Converts the temp reading from the AM2315 to a signed int.
        """

        signednum = 0

        # If we have the negative temp bit set
        if (unsigned & 0x8000) == 0x8000:
            # Clear the negative sign bit, and make the number negative.
           signednum = 0 - (unsigned & 0x7fff)
        else:
            signednum = unsigned

        # Return the unsigned int.
        return signednum

    def get_temp_humid(self):
        """
        get_temp_humid()

        Get the temperature and humidity from the sensor. Returns an array with two integers - temp. [0] and humidity [1]
        """
        # Loop sentinel values
        failCount = 0
        # Commands to get data temp and humidity data from AM2315
        cmd_data = bytearray((self.cmdReadReg, 0x00, 0x04))
        # If we have failed more than twice to read the data, or have finished getting data break the loop.
        while (failCount < 2):
            try:
                cmd_msgs = [I2C.Message(cmd_data)]
                self.__i2c_master.transfer(self.i2c_addr, cmd_msgs)

                # Wait for the sensor to supply data to read.
                time.sleep(0.1)

                # Now read 8 bytes from the AM2315.
                read_data = bytearray((0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00))
                read_msgs = [I2C.Message(read_data, read=True)]
                self.__i2c_master.transfer(self.i2c_addr, read_msgs)

                # Break the string we want out of the array the transaction returns.
                rawTH = bytearray(read_msgs[0].data)

                # Confirm the command worked by checking the response for the command we executed
                # and the number of bytes we asked for.
                if (rawTH[0] == self.cmdReadReg) and (rawTH[1] == 0x04):
                    # And the MSB and LSB for each value together to yield our raw values.
                    humidRaw = (rawTH[2] << 8) | rawTH[3]

                    # Get signed int from AND'd temperature bytes.
                    tempRaw = self.get_signed((rawTH[4] << 8) | rawTH[5])

                    # The return data is scaled up by 10x, so compensate.
                    return (tempRaw / 10.0, humidRaw / 10.0)
            # No connection yet
            except AttributeError:
               pass
            # We usually fail to read data 50% of the time because the sensor goes to sleep, so try twice.
            except IOError:
                if failCount > 1:
                    raise IOError("am2315 IO Error: failed to read from sensor.")
                else:
                    failCount = failCount + 1
        return None, None