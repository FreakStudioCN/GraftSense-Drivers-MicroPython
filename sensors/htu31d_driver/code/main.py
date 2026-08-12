# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : FreakStudio
# @File    : main.py
# @Description : HTU31D driver test for RP2040

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from htu31d import HTU31D

# ======================================== 全局变量 ============================================

I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQUENCY = 100000
I2C_ADDRESS = 0x40
SAMPLE_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

sensor = None

# Hardware setup

time.sleep(3)
print("FreakStudio: HTU31D temperature and humidity sensor driver test")
i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQUENCY)
print("Scanning I2C bus...")
devices = i2c.scan()
print("Found devices: %s" % [hex(device) for device in devices])
if I2C_ADDRESS not in devices:
    raise RuntimeError("HTU31D not found at 0x%02X" % I2C_ADDRESS)
sensor = HTU31D(i2c, address=I2C_ADDRESS, debug=False)
print("Serial number: %s" % sensor.serial_number[0])
print("Humidity resolution: %s" % sensor.humidity_resolution)
print("Temperature resolution: %s" % sensor.temp_resolution)
last_print_time = time.ticks_ms()

# ========================================  主程序 ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= SAMPLE_INTERVAL_MS:
            temperature, humidity = sensor.measurements
            print("Temperature: %.2f C | Humidity: %.2f %%RH" % (temperature, humidity))
            last_print_time = current_time
        time.sleep_ms(100)
except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % error)
except RuntimeError as error:
    print("Runtime error: %s" % error)
finally:
    if sensor is not None:
        sensor.deinit()
    print("Program exited")
