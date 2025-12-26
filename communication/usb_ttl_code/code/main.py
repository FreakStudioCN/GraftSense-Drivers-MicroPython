# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/04 10:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : 串口回环测试代码

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin
import time

# ======================================== 全局变量 ============================================

# 测试消息计数器
count = 1

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时 3 秒
time.sleep(3)
print("FreakStudio: UART loopback test started. Sending data every 2 seconds...")

# 初始化 UART1：TX=Pin8，RX=Pin9，波特率9600
uart = UART(0, baudrate=9600, tx=Pin(8), rx=Pin(9))

# ========================================  主程序  ===========================================

try:
    while True:
        # 构造带计数器的测试消息
        test_msg = f"Test message {count}: Hello, UART loopback!"
        print(f"\nSent: {test_msg}")

        # 发送消息
        uart.write(test_msg.encode('utf-8'))

        # 等待短时间以接收数据
        time.sleep(0.1)

        # 读取并打印接收到的数据
        if uart.any():
            received = uart.read(uart.any()).decode('utf-8')
            print(f"Received: {received}")
        else:
            print("Received: No data (check connections)")

        # 计数器自增并在下一次发送前等待 2 秒
        count += 1
        time.sleep(2)

except KeyboardInterrupt:
    # 捕获键盘中断，结束测试
    print("\nTest stopped by user")
