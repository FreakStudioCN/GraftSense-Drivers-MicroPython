# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : air530z测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import UART, Pin
from air530z import Air530Z, NMEASender
from nemapar import NMEAParser

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio: air530z test")

# 初始化 UART 通信（按硬件实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 创建 HC14_Lora 实例
gps = Air530Z(uart0)

# ========================================  主程序  ===========================================

while True:
    gps_data = gps.read()
    if gps_data:
        print("=" * 40)
        print("GPS_DATA")
        print("=" * 40)

        # 坐标
        # 经度
        print(f"longitude: {gps_data['longitude']}°")
        # 纬度
        print(f"latitude: {gps_data['latitude']}°")

        # 海拔
        print(f"altitude: {gps_data['altitude']}")
        # 时间
        if gps_data['timestamp'] is None:
            print("time:None")
        else:
            ts = gps_data['timestamp']
            print(f"time: {ts['hour']:02d}:{ts['minute']:02d}:{ts['second']:02d}")

        # 卫星
        print(f"satellites: {gps_data['satellites']}")
        print("=" * 40)
    time.sleep(1)


