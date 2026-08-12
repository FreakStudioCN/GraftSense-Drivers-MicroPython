# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 12:00
# @Author  : rdagger
# @File    : demo_heading.py
# @Description : BNO085 UART-RVC heading example for RP2040
# @License : MIT

__version__ = "1.0.0"
__author__ = "rdagger"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, UART

from bno085 import BNO085, BNO085TimeoutError

# ======================================== 全局变量 ============================================

UART_ID = 1
UART_TX_PIN = 4
UART_RX_PIN = 5
UART_BAUDRATE = 115200
READ_INTERVAL_S = 0.1

# ======================================== 功能函数 ============================================


def print_heading_data(data: tuple) -> None:
    yaw, pitch, roll, x_accel, y_accel, z_accel = data
    print("Yaw: {:+7.2f} deg  Pitch: {:+7.2f} deg  Roll: {:+7.2f} deg".format(yaw, pitch, roll))
    print("Accel X: {:+6.2f} m/s^2  Y: {:+6.2f} m/s^2  Z: {:+6.2f} m/s^2".format(x_accel, y_accel, z_accel))
    print("--------------------------------------------")


def main() -> None:
    uart = UART(UART_ID, UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
    sensor = BNO085(uart, timeout=1.0)
    print("BNO085 heading demo started")
    print("UART%d TX=GP%d RX=GP%d baud=%d" % (UART_ID, UART_TX_PIN, UART_RX_PIN, UART_BAUDRATE))

    try:
        while True:
            try:
                print_heading_data(sensor.heading)
            except BNO085TimeoutError:
                print("Warning: read timeout, check UART-RVC wiring")
            time.sleep(READ_INTERVAL_S)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        sensor.deinit()
        uart.deinit()
        print("Program exited")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序 ============================================

if __name__ == "__main__":
    main()
