# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 09:00
# @Author  : Nelio Goncalves Godoi
# @File    : main.py
# @Description : 测试VEML6075紫外线传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from veml6075 import VEML6075

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x10]
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100_000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using VEML6075 UV sensor ...")

# 初始化软件 I2C 总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线设备
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
        sensor = VEML6075(i2c=i2c_bus)
        print("Sensor initialization successful")
        break

if sensor is None:
    raise RuntimeError("No target sensor found on I2C bus")

# ========================================  主程序  ===========================================

try:
    while True:
        print("UVA: %.2f" % sensor.uva)
        print("UVB: %.2f" % sensor.uvb)
        print("UV Index: %.2f" % sensor.uv_index)
        print("Integration time: %d ms" % sensor.integration_time)
        print("---")
        time.sleep_ms(1000)

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
