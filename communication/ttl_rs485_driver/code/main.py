# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/4 下午5:16
# @Author  : 缪贵成
# @File    : main.py
# @Description : ttl转rs485驱动测试程序

# ======================================== 导入相关模块 =========================================

import time
from machine import UART, Pin
from ttl_rs485 import TTL_RS485

# ======================================== 全局变量 ============================================

VALID_ROLES = ("master", "slave")

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:TTL to RS485 module test")
# 角色选择
# 发送端: role = 'master'
# 接收端: role = 'slave'
# 修改为 'slave' 即为接收端
role = 'master'
if role not in VALID_ROLES:
    raise ValueError("Invalid role! Must be one of %s, but got '%s'" % (VALID_ROLES, role))
uart0 = UART(1, baudrate=115200)
uart0.init(baudrate=115200, bits=8, tx=Pin(0), rx=Pin(1), parity=None, stop=1)

rs485 = TTL_RS485(uart0, debug=True)
print("=== TTL_RS485 Test Started: Role -> %s ===" % role)

# ========================================  主程序  ============================================

try:
    if role == 'master':
        count = 0
        while True:
            count += 1
            # 前两个固定参数,count取第八位作为第三个字节，右移八位取第八位作为第四个字节
            test_data = bytes([0x01, 0x02, count & 0xFF, (count >> 8) & 0xFF])
            print("[Loop %d] Sending data: %s" % (count, test_data.hex()))

            # 发送并等待回传
            received = rs485.write_then_read(test_data, rx_expected=len(test_data), timeout_ms=500)
            print("Received back:", received.hex())

            if received == test_data:
                print("loop:Data verified successfully")
            else:
                print("loop:data verified failed")

            time.sleep(2)

    elif role == 'slave':
        while True:
            data_in = rs485.read(timeout_ms=500)
            if data_in:
                print("Received data:", data_in.hex())
                # 回传收到的数据
                rs485.send(data_in)
                print("Data echoed back")
            time.sleep(0.01)

except KeyboardInterrupt:
    print("===program Stopped===")
finally:
    rs485.close()
