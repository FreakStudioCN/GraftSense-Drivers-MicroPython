# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : transparent.py
# @Description : cc253x_ttl 透明传输测试文件

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
import time
from machine import UART, Pin

# 导入第三方驱动模块
from cc253x_ttl import CC253xTTL

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio： cc253x_ttl transparent test")

# 声明串口实例
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# 协调器
cor = CC253xTTL(uart0)
# 路由器
env = CC253xTTL(uart1)

# 将路由器与协调器设置成相同PAMID
while cor.read_status() is None:
    pass
while env.read_status() is None:
    pass

# 获取协调器PAMID与通道
pamid, ch = cor.read_panid_channel()
print(f"cor:pamid:{pamid},channel:{ch}")

while env.set_panid(int(pamid, 16)) is False:
    pass
while env.set_channel(int(ch, 16)) is False:
    pass

# 输出路由器PAMID与通道
time.sleep(0.5)
pamid, ch = env.read_panid_channel()
print(f"env:pamid:{pamid},channel:{ch}")

# ========================================  主程序  ===========================================

while True:
    # 路由器发送
    cor.send_transparent("Here is transparent")
    time.sleep(0.5)

    # 协调器接收并且输出
    mode, data, addr1, addr2 = env.recv_frame()
    print("Coordinator Received Data:")
    print(f"   Mode: {mode}")
    print(f"   Data: {data}")
    print(f"   Address 1: {addr1}")
    print(f"   Address 2: {addr2}")
    time.sleep(1)
