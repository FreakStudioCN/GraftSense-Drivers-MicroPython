# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/23 下午4:18
# @Author  : 缪贵成
# @File    : main.py
# @Description : BH1750光照强度传感器测试文件

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time
from bh_1750 import BH1750

# ======================================== 全局变量 ============================================

bh_addr = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: test Light Intensity Sensor now")

# 初始化I2C总线，使用I2C0外设，SCL引脚为5，SDA引脚为4，频率为100kHz
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print("START I2C SCANNER")
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    # 遍历从机设备地址列表
    print("i2c devices found:", len(devices_list))
for device in devices_list:
    # 判断设备地址是否为的BH_1750地址
    if 0x21 <= device <= 0x5E:
        # 假设第一个找到的设备是BH_1750地址
        print("I2c hexadecimal address:", hex(device))
        bh_addr = device


sensor = BH1750(bh_addr, i2c)

# ========================================  主程序  ============================================

print("one time measure")
sensor.configure(measurement_mode=BH1750.MEASUREMENT_MODE_ONE_TIME, resolution=BH1750.RESOLUTION_HIGH, measurement_time=69)
for i in range(5):
    lux = sensor.measurement
    print("One-time lux =", lux)
    time.sleep(1)

time.sleep(2)

# --- Continuous measurement test ---
print("\n>>> Continuous measurement mode <<<")
sensor.configure(measurement_mode=BH1750.MEASUREMENT_MODE_CONTINUOUSLY, resolution=BH1750.RESOLUTION_HIGH, measurement_time=69)
for i in range(5):
    lux = sensor.measurement
    print("Continuous lux =", lux)
    time.sleep(1)

time.sleep(2)

# --- Generator test ---
print("\n>>> Generator mode <<<")
gen = sensor.measurements()
for i in range(5):
    lux = next(gen)
    print("Generator lux =", lux)

print("\nTest finished.")
