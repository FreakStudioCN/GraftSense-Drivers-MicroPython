# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : alankrantas
# @File    : GPS.py
# @Description : SIM7600模块GPS功能示例，实现GPS开关、北斗卫星选择、搜星及GPS信息查询

# ======================================== 导入相关模块 =========================================

# 导入SIM7600核心类
from sim7600 import SIM7600

# 从sim7600模块导入GPS功能类
from sim7600 import GPS

# 从machine模块导入UART和Pin类，用于硬件引脚和串口配置
from machine import UART, Pin

# 导入time模块，用于延时操作
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保SIM7600模块完成初始化
time.sleep(3)
# 打印GPS模块初始化完成提示信息
print("FreakStudio: SIM7600 GPS module initialized successfully")
# 配置UART0串口，波特率115200，TX引脚16，RX引脚17（适配Raspberry Pi Pico）
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
# 实例化SIM7600核心类，传入配置好的UART对象
sim7600 = SIM7600(uart)
# 实例化GPS功能类，传入SIM7600核心实例
gps = GPS(sim7600)

# ========================================  主程序  ============================================

# 打印GPS操作示例标题
print("=== GPS Operation Example ===")
# 关闭GPS功能并打印操作结果
print(gps.disable_gps())
# 选择北斗卫星系统并打印操作结果
print(gps.set_satellite_beidou())
# 打开GPS功能并打印操作结果
print(gps.enable_gps())

# 开始搜星操作并打印操作结果
print(gps.start_search_satellite())

# 查询GPS信息并打印结果
print(gps.get_gps_info())
