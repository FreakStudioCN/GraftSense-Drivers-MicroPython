# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/30 下午6:10
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : DPS310气压传感器I2C自动扫描识别与气压数据实时读取程序

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, SoftI2C
from micropython_dps310 import dps310

# ======================================== 全局变量 ============================================

TARGET_DPS310_ADDRS = [0x76, 0x77]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: DPS310 Pressure Sensor I2C Auto Scan and Read")

I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100_000
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print(f"i2c devices found: {len(devices_list)}")

sensor = None
for device in devices_list:
    if device in TARGET_DPS310_ADDRS:
        print(f"I2c hexadecimal address: {hex(device)}")
        try:
            sensor = dps310.DPS310(i2c=i2c_bus, address=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================
while True:
    print(f"Pressure: {sensor.pressure}HPa")
    print()
    time.sleep(1)
