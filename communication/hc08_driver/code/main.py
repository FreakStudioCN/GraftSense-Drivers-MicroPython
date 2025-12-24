# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : hc08测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import UART, Pin
from hc08 import HC08

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio:HC08 test")

# 初始化 UART 通信（按硬件实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 创建 HC14_Lora 实例
hc0 = HC08(uart0)

# ========================================  主程序  ===========================================]

ok, resp = hc0.get_version()
print(f'hc0 version:{resp}')
ok, resp = hc0.get_role()
print(f'hc0 role   :{resp}')


while True:
    # 阻塞接收透传数据
    ok, data=hc0.recv_data(timeout_ms=200)
    # 当有数据成功接收打印data，并回传
    if ok:
        print(data)
        hc0.send_data("get data：")
        hc0.send_data(data)
    time.sleep(0.05)

