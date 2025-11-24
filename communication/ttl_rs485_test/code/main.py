# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/04 10:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : 485串口环回测试代码

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin
import time

# ======================================== 全局变量 ============================================
# Initialize UART1: TX=Pin8, RX=Pin9, baud rate 9600
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# Counter for test messages
count = 1
# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 上电延时3s
time.sleep(3)

print("FreakStudio: UART loopback test started. Sending data every 2 seconds...")

# ========================================  主程序  ===========================================

try:
    while True:
        # Create test message with counter
        test_msg = f"Test message {count}: Hello, UART loopback!"
        print(f"\nSent: {test_msg}")
        
        # Send the message
        uart.write(test_msg.encode('utf-8'))
        
        # Wait a short time for data to be received
        time.sleep(0.1)
        
        # Read and print received data
        if uart.any():
            received = uart.read(uart.any()).decode('utf-8')
            print(f"Received: {received}")
        else:
            print("Received: No data (check connections)")
        
        # Increment counter and wait 2 seconds before next send
        count += 1
        time.sleep(2)

except KeyboardInterrupt:
    print("\nTest stopped by user")
