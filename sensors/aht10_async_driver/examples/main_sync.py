# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 16:21
# @Author  : Andreas Bühl
# @File    : main.py
# @Description : 测试 AHT10 温湿度传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import utime
from machine import I2C, Pin

from aht10 import AHT10

# ======================================== 全局变量 ============================================

# AHT10 默认 I2C 地址
AHT10_I2C_ADDR = 0x38

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

utime.sleep(3)
print("FreakStudio: Testing AHT10 temperature and humidity sensor ...")

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)

# I2C 设备扫描，验证传感器是否存在
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found")
# AHT10 无芯片 ID 寄存器，通过地址扫描确认设备存在
if AHT10_I2C_ADDR not in devices:
    raise RuntimeError("AHT10 not found at address 0x%02X" % AHT10_I2C_ADDR)
print("AHT10 found at address 0x%02X" % AHT10_I2C_ADDR)

# 传感器实例化（含内部复位和初始化）
sensor = AHT10(i2c)

# ========================================  主程序  ===========================================

try:
    while True:
        # 读取并打印温度值（℃）
        print("Temperature: {:.2f} C".format(sensor.temperature))
        # 读取并打印湿度值（%）
        print("Humidity: {:.2f} %".format(sensor.relative_humidity))
        print()
        # 每 2 秒采样一次
        utime.sleep(2)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    del i2c
    print("Program exited")
