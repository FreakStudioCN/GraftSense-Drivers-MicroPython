# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : hc14_lora测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import UART, Pin
from hc14_lora import HC14_Lora

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时 3s，给模块稳定时间
time.sleep(3)

# KEY 引脚拉低，进入AT模式
key0 = Pin(2, Pin.OUT)
key0.value(0)

print("FreakStudio: HC14_Lora Test Start")

# 初始化 UART 通信（按硬件实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))

# 创建 HC14_Lora 实例
hc0 = HC14_Lora(uart0)

# ======================================== 主程序 ===========================================

# 测试 AT 通信
ok, resp = hc0.test_comm()
if ok:
    print("[OK] AT 通信正常:", resp)
else:
    print("[ERR] AT 通信失败")

# 获取固件版本
ok, resp = hc0.get_version()
if ok:
    print("固件版本:", resp)

# 获取所有关键参数
ok, params = hc0.get_params()
if ok:
    print("当前参数:", params)

key0.value(1)
time.sleep(0.25)

print("进入透传模式，等待接收数据...")

while True:
    ok, resp = hc0.transparent_recv()
    if not ok:
        continue
    else:
        try:
            msg = resp.decode("utf-8")
        except UnicodeError:
            msg = str(resp)
        print("收到:", msg)

        # 回发带前缀的数据
        reply = f"pico:{msg}".encode("utf-8")
        hc0.transparent_send(reply)
        print("发送:", reply)