# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 12:00
# @Author  : Kai Fricke
# @File    : main.py
# @Description : Test the SHT31 temperature and humidity sensor driver
# @License : MIT

# ==================== 导入相关模块 ====================
from machine import I2C, Pin
import time
from sht31 import SHT31

# ==================== 全局变量 ====================

SHT31_ADDR = 0x44
_PRINT_INTERVAL_MS = 2000
_last_print_time = 0

# ==================== 功能函数 ====================

# ==================== 自定义类 ====================

# ==================== 初始化配置 ====================

time.sleep(3)
print("FreakStudio: Testing SHT31 driver module")

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
devices = i2c.scan()
print("Devices found: %s" % [hex(device) for device in devices])

if not devices:
    raise RuntimeError("No I2C device found on bus")
if SHT31_ADDR not in devices:
    message = "SHT31 not found at expected address 0x%02X" % SHT31_ADDR
    raise RuntimeError(message)

sensor = SHT31(i2c, addr=SHT31_ADDR, debug=False)
_last_print_time = time.ticks_ms()
print("SHT31 sensor initialized successfully")

# ====================  主程序  ====================

try:
    while True:
        current_time = time.ticks_ms()
        elapsed_ms = time.ticks_diff(current_time, _last_print_time)
        if elapsed_ms >= _PRINT_INTERVAL_MS:
            temperature, humidity = sensor.get_temp_humi()
            print("T=%.2f C  RH=%.2f %%" % (temperature, humidity))
            _last_print_time = current_time

        # Optional manual test snippets:
        # - Repeatability: call sensor.get_temp_humi() with SHT31.R_HIGH,
        #   SHT31.R_MEDIUM, or SHT31.R_LOW.
        # - Fahrenheit: call sensor.get_temp_humi(celsius=False).
        # - No clock stretch: call sensor.get_temp_humi(clock_stretch=False).
        # - Invalid params: call sensor.get_temp_humi(resolution=99)
        #   in try/except.

        time.sleep_ms(100)
except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % error)
except Exception as error:
    print("Unknown error: %s" % error)
finally:
    sensor.deinit()
    print("Program exited")
