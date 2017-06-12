/*
Description:
This is a example code for Sandbox Electronics NDIR CO2 sensor module.
You can get one of those products on
http://sandboxelectronics.com

Version:
V1.0

Release Date:
2016-03-30

Author:
Tiequan Shao          info@sandboxelectronics.com

Lisence:
CC BY-NC-SA 3.0

Please keep the above information when you use this code in your project.

Modified by OpenAg to add power_off and power_on functions
*/

#ifndef _NDIR_I2C_H_
#define _NDIR_I2C_H_

class NDIR_I2C {
    public:
		NDIR_I2C(uint8_t i2c_addr);

        uint8_t  i2c_addr;
        uint32_t ppm;

        uint8_t  begin();
        uint8_t  measure();
        uint8_t  ping();

        uint8_t  power_off();
        uint8_t  power_on();

    private:
	    static uint8_t cmd_measure[9];

        uint8_t  send(uint8_t *pdata, uint8_t n);
        uint8_t  receive(uint8_t *pbuf, uint8_t n);
        uint8_t  read_register(uint8_t reg_addr, uint8_t *pval);
        uint8_t  write_register(uint8_t reg_addr, uint8_t *pdata, uint8_t n);
        uint8_t  write_register(uint8_t reg_addr, uint8_t val);
        uint8_t  parse (uint8_t *pbuf);
};
#endif
