# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 使用LIS3MDL磁力计传感器读取磁场数据并打印
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from micropython_lis3mdl import lis3mdl

# ======================================== 全局变量 ============================================

# 目标传感器可能的I2C地址列表（支持多地址）
TARGET_SENSOR_ADDRS: list[int] = [0x1C, 0x1E]

# I2C总线使用的SDA引脚号
I2C_SDA_PIN: int = 4
# I2C总线使用的SCL引脚号
I2C_SCL_PIN: int = 5
# I2C总线通信频率（Hz）
I2C_FREQ: int = 400000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: LIS3MDL sensor auto scan and data acquisition")
# 创建软件I2C总线实例
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描I2C总线上的所有设备地址
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查是否扫描到任何I2C设备
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 初始化传感器对象占位符
sensor: lis3mdl.LIS3MDL = None

# 遍历扫描到的设备地址，匹配目标地址
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 创建LIS3MDL传感器对象
            sensor = lis3mdl.LIS3MDL(i2c=i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未在总线上发现任何目标传感器地址
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================

# 主循环：每隔0.5秒读取并打印磁场数据
while True:
    mag_x, mag_y, mag_z = sensor.magnetic
    print(f"X:{mag_x:0.2f}, Y:{mag_y:0.2f}, Z:{mag_z:0.2f} uT")
    print("")
    time.sleep(0.5)
