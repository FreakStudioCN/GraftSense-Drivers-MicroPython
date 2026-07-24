# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 12:00
# @Author  : rdagger
# @File    : main.py
# @Description : BNO085 UART-RVC test entry for RP2040
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin, UART

import bno085
from bno085 import BNO085, BNO085TimeoutError

# ======================================== 全局变量 ============================================

I2C_ID = 0
I2C_SCL_PIN = 1
I2C_SDA_PIN = 0
I2C_FREQ = 100000
BNO085_I2C_ADDRESS = 0x4A

UART_ID = 1
UART_TX_PIN = 4
UART_RX_PIN = 5
UART_BAUDRATE = 115200

READ_INTERVAL_MS = 200
DRIVER_TIMEOUT_S = 1.0
last_print_time = 0

# ======================================== 功能函数 ============================================


def format_addresses(addresses: list) -> str:
    if not isinstance(addresses, list):
        raise ValueError("addresses must be a list")
    if not addresses:
        return "none"
    return ", ".join("0x%02X" % address for address in addresses)


def print_heading_data(data: tuple) -> None:
    if not isinstance(data, tuple):
        raise ValueError("data must be a tuple")
    yaw, pitch, roll, x_accel, y_accel, z_accel = data
    print("Yaw: {:+7.2f} deg  Pitch: {:+7.2f} deg  Roll: {:+7.2f} deg".format(yaw, pitch, roll))
    print("Accel X: {:+6.2f} m/s^2  Y: {:+6.2f} m/s^2  Z: {:+6.2f} m/s^2".format(x_accel, y_accel, z_accel))
    print("--------------------------------------------")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Testing BNO085 9-DOF IMU sensor on RP2040")
print("Driver version: %s" % bno085.__version__)

i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
uart = UART(UART_ID, UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
sensor = BNO085(uart, timeout=DRIVER_TIMEOUT_S)

print("I2C%d SCL=GP%d SDA=GP%d freq=%d" % (I2C_ID, I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ))
print("UART%d TX=GP%d RX=GP%d baud=%d" % (UART_ID, UART_TX_PIN, UART_RX_PIN, UART_BAUDRATE))

try:
    i2c_addresses = i2c.scan()
    print("I2C scan found: %s" % format_addresses(i2c_addresses))
    if BNO085_I2C_ADDRESS in i2c_addresses:
        print("BNO085 default I2C address 0x%02X found" % BNO085_I2C_ADDRESS)
    else:
        print("BNO085 default I2C address 0x%02X not found" % BNO085_I2C_ADDRESS)
except OSError as error:
    print("I2C scan failed: %s" % error)

print("UART-RVC mode outputs heading automatically; no report enable command is used")
last_print_time = time.ticks_ms()

# ========================================  主程序 ============================================

try:
    print("Reading BNO085 heading data, press Ctrl-C to stop")
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= READ_INTERVAL_MS:
            try:
                print_heading_data(sensor.heading)
            except BNO085TimeoutError:
                print("Warning: read timeout, check UART-RVC wiring and P0 mode pin")
            except OSError as error:
                print("UART communication error: %s" % error)
            last_print_time = current_time
        time.sleep_ms(10)
except KeyboardInterrupt:
    print("Program interrupted by user")
except Exception as error:
    print("Unexpected error: %s" % error)
    raise
finally:
    print("Cleaning up resources")
    sensor.deinit()
    uart.deinit()
    print("Program exited")
