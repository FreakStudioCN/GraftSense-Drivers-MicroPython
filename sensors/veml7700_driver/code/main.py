# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/21 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试VEML7700环境光传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
from veml7700 import VEML7700
import time

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x10]
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100000
INTEGRATION_TIME = 100
SENSOR_GAIN = 1 / 8

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using VEML7700 ambient light sensor ...")

# 初始化软件I2C总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描I2C总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")
if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")
print("I2C devices found: %d" % len(devices_list))

# 遍历扫描结果，初始化目标传感器
sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2C address: %s" % hex(device))
        sensor = VEML7700(
            i2c=i2c_bus,
            address=device,
            it=INTEGRATION_TIME,
            gain=SENSOR_GAIN,
        )
        print("Sensor initialization successful")
        break

if sensor is None:
    raise RuntimeError("No target sensor found on I2C bus")

# 等待第一次积分完成
time.sleep(0.2)

# ========================================  主程序  ===========================================

try:
    while True:
        lux = sensor.read_lux()
        print("Lux: %d lx" % lux)
        time.sleep(1)

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
    print("Program exited")
