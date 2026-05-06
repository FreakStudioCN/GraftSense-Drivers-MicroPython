# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 15:30
# @Author  : FreakStudio
# @File    : main.py
# @Description : Test code for MLX90393 three-axis magnetometer sensor driver
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, I2C
from micropython_mlx90393 import mlx90393

# ======================================== 全局变量 ============================================

# I2C 引脚配置
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5

# 目标传感器 I2C 地址列表
TARGET_SENSOR_ADDRS = [0x0C]

# 测量循环延时（秒）
MEAS_DELAY_S = 1

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: MLX90393 magnetometer test starting ...")

# 初始化 I2C 总线
i2c_bus = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN))

# 扫描 I2C 总线
devices_list = i2c_bus.scan()
print("I2C scan result: %s" % [hex(d) for d in devices_list])

if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")

# 查找目标传感器地址
sensor = None
for device_addr in devices_list:
    if device_addr in TARGET_SENSOR_ADDRS:
        print("Target sensor found at address: %s" % hex(device_addr))
        sensor = mlx90393.MLX90393(i2c=i2c_bus)
        break

if sensor is None:
    raise RuntimeError("Target sensor not found on I2C bus")

print("Sensor initialization successful")

# ========================================  主程序  ===========================================

try:
    while True:
        # 读取 X/Y/Z 三轴磁场值（微特斯拉）
        magx, magy, magz = sensor.magnetic
        print("X: %.2f uT | Y: %.2f uT | Z: %.2f uT" % (magx, magy, magz))
        time.sleep(MEAS_DELAY_S)

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
