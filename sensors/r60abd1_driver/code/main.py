# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/17 16:00
# @Author  : 侯钧瀚
# @File    : mian.py
# @Description : r60abd1毫米波驱动 for micropython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0
# ======================================== 导入相关模块 =========================================

#MicroPython 提供的硬件接口类，用于串口通信和引脚控制模块
from machine import UART, Pin
#关于时间的模块
import time
#R60ABD1 模块驱动类（人体存在/心率/睡眠等传感器协议封装）模块
from r60abd1 import R60ABD1

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def show(label, value, unit=""):
    print(f"→ {label}：{value}{unit}")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# # 打印调试消息
print("FreakStudio: Using R60ABD1 millimeter wave information collection")
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
dev = R60ABD1(uart)

# ========================================  主程序  ===========================================

dev.disable_all_reports()
print("\n【Query output】")
while True:
    val = dev.q_presence();            show("The existence of the human body", "exist" if val==1 else ("Does not exist" if val==0 else None))
    val = dev.q_motion_param();        show("Body movement parameters", val)
    val = dev.q_distance();            show("distance", val, " cm")
    pos = dev.q_position()
    if pos is None:
        show("direction (x,y,z)", None)
    else:
        x,y,z = pos; print(f"→ direction (x, y, z)：({x}, {y}, {z})")
        val = dev.q_hr_value();            show("heart rate", val, " bpm")
        wf = dev.q_hr_waveform()  # -> [-128..127] 的 5 个点，或 None
        if wf:print("HR waveform (centered):", wf)

    val = dev.q_sleep_end_time()
    show("Sleep deadline", val, " minute")
    val = dev.q_struggle_sensitivity()
    if val is None:
        show("Struggle sensitivity", None)
    else:
        mapping = {0:"low",1:"middle",2:"high"}; show("Struggle sensitivity", mapping.get(val, f"Unknown({val})"))

