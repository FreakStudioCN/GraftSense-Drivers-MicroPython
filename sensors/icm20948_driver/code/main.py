# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : RP2040 test entry for the ICM20948 MicroPython driver.

# ======================================== 导入相关模块 =========================================

import time

from machine import I2C, Pin
from micropython_icm20948 import ICM20948

# ======================================== 全局变量 ============================================

I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
ICM20948_ADDRESS = 0x68
READ_INTERVAL_MS = 1000

# ======================================== 功能函数 ============================================


def format_addresses(addresses: list) -> list:
    if not isinstance(addresses, list):
        raise ValueError("addresses must be list")
    return ["0x%02X" % address for address in addresses]


def print_sensor_data(sensor) -> None:
    if not hasattr(sensor, "acceleration"):
        raise ValueError("sensor must provide acceleration")
    if not hasattr(sensor, "gyro"):
        raise ValueError("sensor must provide gyro")
    if not hasattr(sensor, "temperature"):
        raise ValueError("sensor must provide temperature")

    acc_x, acc_y, acc_z = sensor.acceleration
    gyro_x, gyro_y, gyro_z = sensor.gyro
    temperature = sensor.temperature

    print("Accel (m/s^2): x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z))
    print("Gyro  (rad/s): x=%.4f, y=%.4f, z=%.4f" % (gyro_x, gyro_y, gyro_z))
    print("Temperature C: %.2f" % temperature)
    print("-" * 40)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: ICM20948 9-Axis Sensor Test")

i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
print("I2C bus initialized: id=%d, scl=GP%d, sda=GP%d" % (I2C_ID, I2C_SCL_PIN, I2C_SDA_PIN))

try:
    i2c_devices = i2c.scan()
    print("I2C devices found: %s" % format_addresses(i2c_devices))
    if ICM20948_ADDRESS not in i2c_devices:
        raise RuntimeError("ICM20948 address 0x%02X was not found" % ICM20948_ADDRESS)
    icm = ICM20948(i2c, address=ICM20948_ADDRESS, debug=False)
    print("ICM20948 initialized at address 0x%02X" % ICM20948_ADDRESS)
except OSError as exc:
    print("I2C initialization failed: %s" % exc)
    raise
except Exception as exc:
    print("Sensor initialization failed: %s" % exc)
    raise

# ========================================  主程序 ============================================

try:
    while True:
        try:
            print_sensor_data(icm)
        except OSError as exc:
            print("I2C read failed: %s" % exc)
        except Exception as exc:
            print("Sensor read failed: %s" % exc)
        time.sleep_ms(READ_INTERVAL_MS)
except KeyboardInterrupt:
    print("Program interrupted by user")
finally:
    try:
        icm.deinit()
    except Exception as exc:
        print("Sensor cleanup failed: %s" % exc)
    print("Program exited")
