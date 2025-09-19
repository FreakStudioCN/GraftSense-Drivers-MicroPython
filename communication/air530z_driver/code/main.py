# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : air530z测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import UART,Pin
from air530z import Air530Z

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
#time.sleep(3)
print("FreakStudio: air530z test")

# 初始化 UART 通信（按硬件实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
# 创建 HC14_Lora 实例
gps = Air530Z(uart0)

gps._send()
# ========================================  主程序  ===========================================
while True:
    ok,resp = gps._recv()
    if ok:
        print(resp)
        for i in resp:
            parsed_sentence = gps.update(i)

        # 每解析1个有效句子，输出一次关键数据
        if parsed_sentence :  # 仅当定位有效时输出
            print("="*50)
            print(f"解析句子类型：{parsed_sentence}")
            print(f"本地时间：{gps.timestamp[0]:02d}:{gps.timestamp[1]:02d}:{gps.timestamp[2]:.1f}")
            print(f"本地日期：{gps.date_string(formatting='s_dmy', century='20')}")
            print(f"纬度：{gps.latitude_string()}")
            print(f"经度：{gps.longitude_string()}")
            print(f"速度：{gps.speed_string(unit='kph')}")
            print(f"海拔：{gps.altitude} 米")
            print(f"使用卫星数：{gps.satellites_in_use} 颗")
            print("="*50)
