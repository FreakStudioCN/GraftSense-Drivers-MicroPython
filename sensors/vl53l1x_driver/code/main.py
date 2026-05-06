# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 07:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : VL53L1X 激光测距传感器驱动测试
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from vl53l1x import VL53L1X

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x29]
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400_000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: VL53L1X distance measurement test")

# ========================================  主程序  ============================================

if __name__ == '__main__':
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

    devices_list = i2c_bus.scan()
    print("START I2C SCANNER")

    if not devices_list:
        raise SystemExit("I2C scan found no devices")
    print("i2c devices found:", len(devices_list))

    sensor = None
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2C address:", hex(device))
            try:
                sensor = VL53L1X(i2c=i2c_bus, address=device)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print("Sensor init failed:", e)

    if sensor is None:
        raise SystemExit("No target sensor found on I2C bus")

    try:
        while True:
            distance_mm = sensor.read()
            print("range: %d mm" % distance_mm)
            time.sleep_ms(50)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        sensor.deinit()
        print("Sensor deinitialized")
