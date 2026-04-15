# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/15 下午2:30
# @Author  : hogeiha
# @File    : main.py
# @Description : HX711称重传感器校准与测量程序，支持去皮、标定和实时重量显示

# ======================================== 导入相关模块 =========================================
from hx711_gpio import HX711
from machine import Pin
import time

# ======================================== 全局变量 ============================================
# 校准砝码重量，单位克
CAL_WEIGHT = 100

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
# 等待系统稳定
time.sleep(3)
print("FreakStudio: HX711 sensor initialization starting")

# 定义数据引脚和时钟引脚
# 6 = DATA, 7 = SCK
pin_DATA = Pin(6, Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin(7, Pin.OUT)

# 初始化HX711传感器
try:
    hx = HX711(pin_SCK, pin_DATA, gain=128)
    print("HX711 initialization successful")
    time.sleep(1)
except Exception as e:
    print("Sensor initialization failed:", e)
    while True:
        pass

# ========================================  主程序  ============================================
# 执行去皮操作
print("Please keep no load, starting tare...")
time.sleep(2)

# 读取20次平均值作为偏移量
offset = hx.read_average(times=20)
hx.set_offset(offset)
# 同步滤波基线值
hx.filtered = offset
print("Tare completed")
print("Zero offset value:", offset)

# 校准流程：放置标准砝码
input("Please put the standard weight and press Enter to continue...")
time.sleep(2)

# 读取加载砝码后的20次平均值
cal_raw = hx.read_average(times=20)
net_raw = cal_raw - hx.OFFSET

print("Raw value after loading:", cal_raw)
print("Net increment:", net_raw)

# 检查校准增量是否过小
if abs(net_raw) < 1000:
    raise ValueError("Calibration increment too small, please check HX711 wiring, sensor connection or weight correctness")

# 计算转换系数并设置
scale_factor = net_raw / CAL_WEIGHT
hx.set_scale(scale_factor)

print("Calibration completed")
print("SCALE =", scale_factor)
print("----------------------------------------")

# 再次同步滤波，避免刚校准完前几次读数漂移
hx.filtered = hx.read_average(times=10)

# 主循环：持续读取并显示重量
while True:
    raw_value = hx.read()
    weight = hx.get_units()
    print("Raw value: {:>10.0f} | Weight: {:>8.2f} g".format(raw_value, weight))
    time.sleep(0.2)
