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
        resp (iterable): Sequence of NMEA sentences.  

    Processing:
        - Iterate through NMEA sentences, call gps.update() on each.  
        - If a valid fix is parsed, print timestamp, date, latitude, longitude, speed, altitude, and satellites in use.  
    """
    gps.feed(resp)

    print(f"本地时间：{gps.data['time']['hour']:02d}:{gps.data['time']['minute']:02d}:{gps.data['time']['second']:02d}")
    print(f"本地日期：{gps.data['date']['day']:02d}/{gps.data['date']['month']:02d}/{gps.data['date']['year']:04d}")
    print(f"纬度：{gps.data['latitude']}")
    print(f"经度：{gps.data['longitude']}")
    print(f"海拔：{gps.data['altitude']} 米")
    print(f"使用卫星数：{gps.data['sats_in_view']} 颗")

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
    if gps._uart.any():
        resp = gps._uart.read()
        resolve(gps, resp)
    time.sleep(1)

