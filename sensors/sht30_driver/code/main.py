# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Roberto Sanchez
# @File    : main.py
# @Description : Test code for the SHT30 temperature and humidity sensor driver
# @License : Apache License 2.0

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin

from sht30 import SHT30

# ======================================== 全局变量 ============================================

# User configuration: change these pins for your RP2040 board wiring.
I2C_BUS_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
SHT30_ADDR = 0x44
PRINT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: SHT30 temperature and humidity sensor test")

i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
print("I2C bus initialized on RP2040 (bus=%d, SCL=GP%d, SDA=GP%d)" % (I2C_BUS_ID, I2C_SCL_PIN, I2C_SDA_PIN))

devices = i2c.scan()
print("I2C scan result: %s" % [hex(device) for device in devices])
if not devices:
    raise RuntimeError("No I2C devices found")
if SHT30_ADDR not in devices:
    raise RuntimeError("SHT30 not found at address 0x%02X" % SHT30_ADDR)

sensor = SHT30(i2c, addr=SHT30_ADDR)
status_value = sensor.status()
print("Status register: 0x%04X" % status_value)
print("Heater: %s" % ("ON" if status_value & SHT30.HEATER_MASK else "OFF"))
print("T alert: %s, RH alert: %s" % (bool(status_value & SHT30.T_ALERT_MASK), bool(status_value & SHT30.RH_ALERT_MASK)))
last_print_time = time.ticks_ms()

# ========================================  主程序 ============================================

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            temperature_c, humidity = sensor.measure()
            print("Temperature: %.2f C, Humidity: %.2f %%" % (temperature_c, humidity))
            last_print_time = current_time
        time.sleep_ms(100)
except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as err:
    print("Hardware communication error: %s" % err)
except Exception as err:
    print("Unexpected error: %s" % err)
finally:
    print("Cleaning up resources")
    sensor.deinit()
    print("Program exited")
