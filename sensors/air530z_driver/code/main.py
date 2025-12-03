# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : air530z测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import UART,Pin
from air530z import Air530Z,NMEASender
from nemapar import NMEAParser

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================
def resolve(gps, resp):
    """
    功能函数：解析 GPS 模块返回的 NMEA 数据，并在解析出有效定位信息时打印关键信息。  

    Args:
        gps (object): GPS 解析对象，提供 update()、timestamp、date_string() 等接口。  
        resp (iterable): NMEA 数据序列，每个元素为一条 NMEA 语句。  

    处理逻辑：
        - 遍历输入的 NMEA 数据，逐条调用 gps.update() 进行解析。  
        - 当解析得到有效结果时，打印时间、日期、经纬度、速度、高度以及卫星数等关键数据。  

    ==========================================
    Utility function: Parse NMEA data from GPS module and print key info when valid fix is obtained.  

    Args:
        gps (object): GPS parser instance with update(), timestamp, date_string(), etc.  
5        resp (iterable): Sequence of NMEA sentences.  

    Processing:
        - Iterate through NMEA sentences, call gps.update() on each.  
        - If a valid fix is parsed, print timestamp, date, latitude, longitude, speed, altitude, and satellites in use.  
    """
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

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio: air530z test")

# 初始化 UART 通信（按硬件实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 创建 HC14_Lora 实例
gps = Air530Z(uart0)
nema = NMEASender()
resolver = NMEAParser()

# ========================================  主程序  ===========================================
while True:
    if gps._uart.any():
        try:
            resp = gps._uart.read()
            print(resp)
            resolver.feed(resp)
            print(resolver.last_known_fix)
        except Exception as e:
            pass
    time.sleep(1)

