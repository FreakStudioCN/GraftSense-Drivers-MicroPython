# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : hc14_lora测试文件

# ======================================== 导入相关模块 =========================================

# 时间相关模块
import time
# 引脚相关模块
from machine import UART, Pin
# 生成随机数模块
import urandom
# 常量模块
from micropython import const
# HC14_Lora 驱动模块
from hc14_lora import HC14_Lora

# ======================================== 全局变量 ============================================

# LoRa 参数配置
# 设置信道
channel = const(7)
# 设置随机发送数据长度
data = const(80)
# 随机生成指定长度的数据等待后续发送
reply = bytes([urandom.getrandbits(8) for _ in range(data)])
# 设置发射功率
power = const(20)
# 设置传输速率
rate = const(7)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时 3s，给模块稳定时间
time.sleep(3)

print("FreakStudio: HC14_Lora Test Start")

# 初始化 UART 通信（按硬件实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# 创建 HC14_Lora 实例
# 接收端
hc0 = HC14_Lora(uart0)
# 发送端
hc1 = HC14_Lora(uart1)

# ======================================== 主程序 ===========================================

#保持按下两个模块按钮进入AT配置模式
# 测试 AT 通信
ok, resp0 = hc0.test_comm()
if ok:
    print("[OK] AT communication normal:", resp0)
    # 配置LoRa模块的通信信道为7
    hc0.set_channel(channel)  
    # 配置LoRa模块的传输速率（具体速率需参考模块手册）
    hc0.set_rate(rate)     
    # 配置LoRa模块的发射功率为20dBm
    hc0.set_power(power)
else:
    print("[ERR] AT communication failed")

# 获取固件版本
ok, resp = hc0.get_version()
if ok:
    print("Firmware version:", resp)
# 获取所有关键参数
ok, params = hc0.get_params()
if ok:
    print("Current parameters:", params)

# 测试 AT 通信
ok, resp1 = hc1.test_comm()
if ok:
    print("[OK] AT communication normal:", resp1)
    # 配置LoRa模块的通信信道为7
    hc1.set_channel(channel)  
    # 配置LoRa模块的传输速率（具体速率需参考模块手册）
    hc1.set_rate(rate)     
    # 配置LoRa模块的发射功率为20dBm
    hc1.set_power(power)
else:
    print("[ERR] AT communication failed")

# 获取固件版本
ok, resp = hc1.get_version()
if ok:
    print("Firmware version:", resp)

# 获取所有关键参数
ok, params = hc1.get_params()
if ok:
    print("Current parameters:", params)

# 等待用户松开按钮进入透传模式
time.sleep(2)
print("Entering transparent mode, waiting for data...")

# 发送数据
hc1.transparent_send(reply)
print("Sent:", reply)
# 记录发送时间
start_ms = time.ticks_ms()
print(f"Start time: {start_ms} ms")

while True:
    # 接收数据
    ok, resp = hc0.transparent_recv()
    if not ok:
        continue
    else:
        try:
            msg = resp.decode("utf-8")
        except UnicodeError:
            msg = str(resp)
        # 记录接收时间
        end_ms = time.ticks_ms()
        # 计算时间差输出
        elapsed_ms = time.ticks_diff(end_ms, start_ms)
        print("Received:", msg)
        print(f"Elapsed time: {elapsed_ms} ms")
