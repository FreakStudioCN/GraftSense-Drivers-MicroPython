# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : OldhamMade
# @File    : main.py
# @Description : RP2040 test program for the LM75 driver
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin

from lm75 import LM75

# ======================================== 全局变量 ============================================

I2C_ID = 0
SCL_PIN = 5
SDA_PIN = 4
I2C_FREQ = 100000
LM75_DEFAULT_ADDR = 0x48
PRINT_INTERVAL_MS = 2000
last_print_time = 0


# ======================================== 功能函数 ============================================


def format_i2c_addresses(addresses):
    """Return a printable list of I2C addresses."""
    return ["0x%02X" % address for address in addresses]


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================

time.sleep(3)

print("FreakStudio: Testing LM75 I2C Temperature Sensor Driver on RP2040")

scl = Pin(SCL_PIN)
sda = Pin(SDA_PIN)
i2c = I2C(I2C_ID, scl=scl, sda=sda, freq=I2C_FREQ)
sensor = None

print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found I2C devices: %s" % format_i2c_addresses(devices))

if LM75_DEFAULT_ADDR not in devices:
    raise RuntimeError("LM75 not found at expected address 0x%02X" % LM75_DEFAULT_ADDR)

print("Verifying LM75 at address 0x%02X..." % LM75_DEFAULT_ADDR)
try:
    verify_buf = bytearray(2)
    i2c.readfrom_mem_into(LM75_DEFAULT_ADDR, 0x00, verify_buf)
    print("LM75 device found and responding")
except OSError as e:
    raise RuntimeError("LM75 device not responding") from e

sensor = LM75(i2c, addr=LM75_DEFAULT_ADDR, debug=False)
last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()

        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            temp_c, point = sensor.get_temp()
            print("Temperature: %d.%d C" % (temp_c, point))

            msb, lsb = sensor.get_output()
            print("Raw: MSB=0x%02X LSB=0x%02X" % (msb, lsb))

            last_print_time = current_time

        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if sensor is not None:
        sensor.deinit()
        del sensor
    print("Program exited")
