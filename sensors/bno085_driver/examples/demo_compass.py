# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 12:00
# @Author  : rdagger
# @File    : demo_compass.py
# @Description : BNO085 UART-RVC compass example for RP2040
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

DIRECTIONS = {
    "North": 0,
    "Northeast": 45,
    "East": 90,
    "Southeast": 135,
    "South": 180,
    "Southwest": -135,
    "West": -90,
    "Northwest": -45,
}

COMPASS_RANGES = (
    (-180.0, -157.5, "South"),
    (-157.5, -112.5, "Southwest"),
    (-112.5, -67.5, "West"),
    (-67.5, -22.5, "Northwest"),
    (-22.5, 22.5, "North"),
    (22.5, 67.5, "Northeast"),
    (67.5, 112.5, "East"),
    (112.5, 157.5, "Southeast"),
    (157.5, 180.0, "South"),
)

# ======================================== 功能函数 ============================================


def get_compass_point(degree: float) -> str:
    if not isinstance(degree, (int, float)):
        raise ValueError("degree must be int or float")
    for low, high, direction in COMPASS_RANGES:
        if low <= degree <= high:
            return direction
    return "North"


def get_offset(degree: float, direction: str) -> str:
    if not isinstance(degree, (int, float)):
        raise ValueError("degree must be int or float")
    if direction not in DIRECTIONS:
        raise ValueError("direction is not valid")
    direction_degree = DIRECTIONS[direction]
    if direction == "South" and degree < 0:
        offset = degree + direction_degree
    else:
        offset = degree - direction_degree
    return ("+" if offset > 0 else "") + "{:.2f}".format(offset)


def main() -> None:
    uart = UART(UART_ID, UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
    sensor = BNO085(uart, timeout=1.0)
    print("BNO085 compass demo started")
    print("UART%d TX=GP%d RX=GP%d baud=%d" % (UART_ID, UART_TX_PIN, UART_RX_PIN, UART_BAUDRATE))

    try:
        while True:
            try:
                yaw = sensor.heading[0]
                direction = get_compass_point(yaw)
                offset = get_offset(yaw, direction)
                print("Heading: {:+7.2f} deg  Direction: {}  Offset: {} deg".format(yaw, direction, offset))
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
