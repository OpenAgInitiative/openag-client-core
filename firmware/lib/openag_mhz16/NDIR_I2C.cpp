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
*/

#include <Wire.h>
#include <NDIR_I2C.h>

//General Registers
#define  RHR        (0x00)
#define  THR        (0X00)
#define  IER        (0X01)
#define  FCR        (0X02)
#define  IIR        (0X02)
#define  LCR        (0X03)
#define  MCR        (0X04)
#define  LSR        (0X05)
#define  MSR        (0X06)
#define  SPR        (0X07)
#define  TCR        (0X06)
#define  TLR        (0X07)
#define  TXLVL      (0X08)
#define  RXLVL      (0X09)
#define  IODIR      (0X0A)
#define  IOSTATE    (0X0B)
#define  IOINTENA   (0X0C)
#define  IOCONTROL  (0X0E)
#define  EFCR       (0X0F)

//Special Registers
#define  DLL        (0x00)
#define  DLH        (0X01)

//Enhanced Registers
#define  EFR        (0X02)
#define  XON1       (0X04)
#define  XON2       (0X05)
#define  XOFF1      (0X06)
#define  XOFF2      (0X07)

//Application Related
#define  SC16IS750_CRYSTCAL_FREQ (14745600UL)
#define  RECEIVE_TIMEOUT         (100)

#if ARDUINO >= 100
    #include "Arduino.h"
#else
    #include "WProgram.h"
#endif

#ifdef __AVR__
 #define WIRE Wire
#else // Arduino Due
 #define WIRE Wire1
#endif

uint8_t NDIR_I2C::cmd_measure[9] = {0xFF,0x01,0x9C,0x00,0x00,0x00,0x00,0x00,0x63};

NDIR_I2C::NDIR_I2C(uint8_t i2c_addr)
{
    if (i2c_addr >= 8 && i2c_addr < 120) {
        NDIR_I2C::i2c_addr = i2c_addr;
    } else {
        NDIR_I2C::i2c_addr = 0;
    }
}


uint8_t NDIR_I2C::begin()
{
    if (i2c_addr) {
        WIRE.begin();
        write_register(IOCONTROL, 0x08);
        write_register(IODIR, 0x03);
        write_register(IOSTATE, 0x03);

        if (write_register(FCR, 0x07)) {
            if (write_register(LCR, 0x83)) {
                if (write_register(DLL, 0x60)) {
                    if (write_register(DLH, 0x00)) {
                        if (write_register(LCR, 0x03)) {
                            if (measure()) {
                                return true;
                            }
                        }
                    }
                }
            }
        }
    }

    return false;
}

uint8_t NDIR_I2C::measure()
{
    uint8_t buf[9];

    if (i2c_addr) {
        if (write_register(FCR, 0x07)) {
            delayMicroseconds(1);

            if (send(cmd_measure, 9)) {
                if (receive(buf, 9)) {
                    if (parse(buf)) {
                        return true;
                    }
                }
            }
        }
    }

    return false;
}

uint8_t NDIR_I2C::ping() {
  uint8_t buf;
  return read_register(IOSTATE, &buf);
}

uint8_t NDIR_I2C::power_off() {
  uint8_t buf;
  if (!read_register(IOSTATE, &buf)) {
    return false;
  }
  buf = buf & ~1;
  return write_register(IOSTATE, buf);
}

uint8_t NDIR_I2C::power_on() {
  uint8_t buf;
  if (!read_register(IOSTATE, &buf)) {
    return false;
  }
  buf = buf | 1;
  return write_register(IOSTATE, buf);
}

uint8_t NDIR_I2C::parse (uint8_t *pbuf)
{
    uint8_t i;
    uint8_t checksum = 0;

    for (i=0; i<9; i++) {
        checksum += pbuf[i];
    }

    if (pbuf[0] == 0xFF && pbuf[1] == 0x9C && checksum == 0xFF) {
        ppm = (uint32_t)pbuf[2] << 24 | (uint32_t)pbuf[3] << 16 | (uint32_t)pbuf[4] << 8 | pbuf[5];
        return true;
    } else {
        return false;
    }
}


uint8_t NDIR_I2C::send(uint8_t *pdata, uint8_t n) {
    uint8_t result;

    if (read_register(TXLVL, &result)) {
        if (result >= n) {
            if (write_register(THR, pdata, n)) {
                return true;
            }
        }
    }

    return false;
}


uint8_t NDIR_I2C::receive(uint8_t *pbuf, uint8_t n) {
    uint8_t  i;
    uint8_t  rx_level;
    uint32_t start = millis();

    while (n) {
        if (read_register(RXLVL, &rx_level)) {
            if (rx_level > n) {
                rx_level = n;
            }

            if (rx_level) {
                WIRE.beginTransmission(i2c_addr);
                WIRE.write(RHR << 3);

                if (WIRE.endTransmission() != 0) {
                    return false;
                }//delay(10);

                if (rx_level == WIRE.requestFrom(i2c_addr, rx_level)) {
                    for (i=0; i<rx_level; i++) {
                       *pbuf = WIRE.read();
                        pbuf++;
                        n--;
                    }
                } else {
                    return false;
                }
            }
        } else {
            return false;
        }

        if (millis() - start > RECEIVE_TIMEOUT) {
            return false;
        }
    }

    return true;
}


uint8_t NDIR_I2C::read_register(uint8_t reg_addr, uint8_t *pval)
{
    WIRE.beginTransmission(i2c_addr);
    WIRE.write(reg_addr << 3);

    if (WIRE.endTransmission() != 0) {
        return false;
    }

    if (WIRE.requestFrom(i2c_addr, (uint8_t)1) != 1) {
        return false;
    }

   *pval = WIRE.read();
    return true;
}


uint8_t NDIR_I2C::write_register(uint8_t reg_addr, uint8_t *pdata, uint8_t n)
{
    WIRE.beginTransmission(i2c_addr);
    WIRE.write(reg_addr << 3);

    while (n--) {
        WIRE.write(*pdata);
        pdata++;
    }

    if (WIRE.endTransmission() != 0) {
        return false;
    } else {
        return true;
    }
}


uint8_t NDIR_I2C::write_register(uint8_t reg_addr, uint8_t val)
{
    return write_register(reg_addr, &val, 1);
}

