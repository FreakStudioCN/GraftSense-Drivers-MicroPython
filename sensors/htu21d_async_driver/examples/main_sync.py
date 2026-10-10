# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 18:51
# @Author  : Julian Hille
# @File    : main.py
# @Description : Test code for HTU21D temperature and humidity sensor driver
# @License : MIT


# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from htu21d import HTU21D


# ======================================== 全局变量 ============================================

# I2C总线配置
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
FREQ = 100000

# 打印间隔（毫秒）
PRINT_INTERVAL_MS = 2000

# HTU21D 设备I2C地址（用于扫描验证）
DEVICE_ADDRESS = 0x40


# ======================================== 功能函数 ============================================


def scan_bus(i2c: I2C) -> list:
    """
    扫描I2C总线并打印已发现的设备地址
    Args:
        i2c (I2C): I2C总线实例
    Returns:
        list: 已发现的I2C设备地址列表
    ==========================================
    Scan I2C bus and print discovered device addresses.
    Args:
        i2c (I2C): I2C bus instance
    Returns:
        list: List of discovered I2C device addresses
    """
    devices = (getattr(i2c, "scan")(),)[0]
    print("I2C devices found: %s" % [hex(addr) for addr in devices])
    return devices


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using HTU21D temperature and humidity sensor ...")

# 创建I2C总线实例
i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=FREQ)

# 扫描I2C总线，验证设备是否在线
devices = scan_bus(i2c)
if len(devices) == 0:
    raise RuntimeError("No I2C device found on bus")

# HTU21D没有芯片ID寄存器，通过扫描地址和后续CRC校验来验证设备
if DEVICE_ADDRESS not in devices:
    raise RuntimeError("HTU21D not found at address 0x%02X. Check VCC, GND, SDA=GP%d, SCL=GP%d." % (DEVICE_ADDRESS, SDA_PIN, SCL_PIN))
print("Device found at address 0x%02X" % DEVICE_ADDRESS)

# 创建传感器驱动实例
sensor = HTU21D(i2c, addr=DEVICE_ADDRESS)


# ========================================  主程序  ===========================================

try:
    last_print_time = time.ticks_ms()
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            try:
                temp = sensor.temperature
                humi = sensor.humidity
                print("Temperature: %.2f C  Humidity: %.2f %%RH" % (temp, humi))
            except RuntimeError as e:
                print("Sensor read error: %s" % str(e))
            last_print_time = current_time
        time.sleep_ms(100)

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
