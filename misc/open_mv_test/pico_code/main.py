# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 15:00
# @Author  : 侯钧瀚
# @File    : mian.py
# @Description : OpenMV Pico UART环回测试代码

# ======================================== 导入相关模块 =========================================

# 导入MicroPython标准库模块
from machine import UART, Pin
import time

# ======================================== 全局变量 ============================================

# 测试消息计数器
count = 1

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio: UART loopback test started. Sending data every 2 seconds...")

# 初始化 UART1：TX=Pin8，RX=Pin9，波特率 9600
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# ========================================  主程序  ==================================

try:
    while True:
        # 发送消息
        # 等待短时间以接收数据
        # 读取并打印接收到的数据
        if uart.any():
            time.sleep(0.2)
            received = uart.read(uart.any()).decode("utf-8")
            print(f"Received: {received}")

except KeyboardInterrupt:
    print("\nTest stopped by user")
