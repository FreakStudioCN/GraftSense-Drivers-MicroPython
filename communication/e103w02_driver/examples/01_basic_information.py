# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/8/20
# @Author  : FreakStudio
# @File    : 01_basic_information.py
# @Description : E103-W02模块基本信息与当前配置查询示例
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.x"

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, UART
from e103w02 import E103W02

# ======================================== 全局变量 ============================================

UART_ID = 0
UART_BAUDRATE = 115200
UART_TX_PIN = 16
UART_RX_PIN = 17

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: E103-W02 basic information example")

uart = UART(
    UART_ID,
    baudrate=UART_BAUDRATE,
    bits=8,
    parity=None,
    stop=1,
    tx=Pin(UART_TX_PIN),
    rx=Pin(UART_RX_PIN),
    timeout=0,
)
device = E103W02(uart)

# ========================================  主程序  ============================================

try:
    device.enter_command_mode()
    try:
        print("Version: %s" % device.get_version())
        print("Device SN: %s" % device.get_device_sn())
        print("MAC: %s" % device.get_mac())
        print("Status: %s" % device.get_status())
        print("Role: %s" % device.get_role())
        print("STA: %s" % device.get_sta())
        print("STA IP: %s" % device.get_sta_ip())
        print("AP: %s" % device.get_ap())
        print("AP IP: %s" % device.get_ap_ip())
        print("AP Channel: %s" % device.get_ap_channel())
        print("Mode: %s" % device.get_mode())
        print("Socket: %s" % device.get_socket())
        print("UART: %s" % device.get_uart_config())
    finally:
        device.exit_command_mode()
except KeyboardInterrupt:
    print("Example stopped by user")
except OSError as exc:
    print("E103-W02 hardware error: %s" % exc)
except Exception as exc:
    print("E103-W02 query failed: %s" % exc)
finally:
    device.deinit()
    del device
    del uart
    print("Example finished")
