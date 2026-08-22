# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/8/20
# @Author  : FreakStudio
# @File    : 02_ap_tcp_server_demo.py
# @Description : E103-W02 AP TCP Server双向透明传输示例
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
SEND_INTERVAL_MS = 2000
RECEIVE_TIMEOUT_MS = 1500

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: E103-W02 AP TCP Server demo")

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
        print("Role: %s" % device.get_role())
        print("AP: %s" % device.get_ap())
        print("AP IP: %s" % device.get_ap_ip())
        print("Socket: %s" % device.get_socket())
    finally:
        device.exit_command_mode()

    print("Connect the PC to the AP, then connect a TCP client to 192.168.1.1:8887")
    count = 1
    while True:
        message = "E103-W02 message %d\r\n" % count
        device.write(message)
        print("Sent: %s" % message.strip())

        response = device.read(timeout_ms=RECEIVE_TIMEOUT_MS)
        if response:
            print("Received: %s" % response)
        else:
            print("No TCP echo received")

        count += 1
        time.sleep_ms(SEND_INTERVAL_MS)
except KeyboardInterrupt:
    print("Demo stopped by user")
except OSError as exc:
    print("E103-W02 hardware error: %s" % exc)
except Exception as exc:
    print("E103-W02 demo failed: %s" % exc)
finally:
    device.deinit()
    del device
    del uart
    print("Demo finished")
