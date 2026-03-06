# EWM550-7G9T10SP UWB模组MicroPython驱动
# -*- coding: utf-8 -*-
# @Time    : 2026/3/2
# @Author  : hogeiha
# @File    : main.py
# @Description : EWM550-7G9T10SP 超宽带UWB测距定位模组驱动，支持AT指令配置、测距、透传模式
# @License : MIT
# @Platform : MicroPython v1.23.0

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin
from ewm550_uwb import EWM550_UWB
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

uart1 = UART(1, baudrate=921600, tx=Pin(8), rx=Pin(9), bits=8, parity=None, stop=1)
ewm550_base = EWM550_UWB(uart1, rx_timeout_ms=600)

print("\n===== Start configuring as base station mode =====")
# 1. 进入AT模式
ok, resp = ewm550_base.enter_at_mode()
print(ok, resp, "Enter AT mode")

# 2. 检测模块通信
ok, resp = ewm550_base.check()
print(ok, resp, "Detect module communication")

# 3. 配置核心参数（与标签地址匹配）
# 设为标签
ok, resp = ewm550_base.set_role(ewm550_base.Role["BASE"])
print(ok, resp, "Set to base station mode")
# 标签源地址：0000（与标签目标地址匹配）
ok, resp = ewm550_base.set_src_addr("0000")
print(ok, resp, "Set tag source address to 0000")

# 目标地址：前4位为基站地址1111，后16位补0（标签仅前4位生效）
ok, resp = ewm550_base.set_dst_addr("11110000000000000000")
print(ok, resp, "Bind base station address to 1111")

# 4. 复位+退出AT模式
ok, resp = ewm550_base.reset_module()
print(ok, resp, "Reset and exit AT mode")

uart = UART(0, baudrate=921600, tx=Pin(16), rx=Pin(17), bits=8, parity=None, stop=1)
ewm550_tag = EWM550_UWB(uart, rx_timeout_ms=600)

print("\n===== Start configuring as tag mode =====")
# 1. 进入AT模式
ok, resp = ewm550_tag.enter_at_mode()
print(ok, resp, "Enter AT mode")

# 2. 检测模块通信
ok, resp = ewm550_tag.check()
print(ok, resp, "Detect module communication")

# 3. 配置核心参数（与基站地址匹配）
# 设为标签
ok, resp = ewm550_tag.set_role(ewm550_tag.Role["TAG"])
print(ok, resp, "Set to tag mode")
# 标签源地址：1111（与基站目标地址匹配）
ok, resp = ewm550_tag.set_src_addr("1111")
print(ok, resp, "Set tag source address to 1111")

# 目标地址：前4位为基站地址0000，后16位补0（标签仅前4位生效）
ok, resp = ewm550_tag.set_dst_addr("00000000000000000000")
print(ok, resp, "Bind base station address to 0000")

# 4. 复位+退出AT模式
ok, resp = ewm550_tag.reset_module()
print(ok, resp, "Reset and exit AT mode")

# ========================================  主程序  ===========================================

while True:
    # 先判断是否有数据
    if uart.any():
        data = uart.read()
        parsed_data = ewm550_tag.parse_ranging_data(data)
        print(parsed_data)
    # 避免占用过多资源
    time.sleep_ms(10)
