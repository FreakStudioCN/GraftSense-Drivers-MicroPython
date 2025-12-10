# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/16 下午8:17
# @Author  : 缪贵成
# @File    : main.py
# @Description : 基于TCS34725的颜色识别模块驱动文件测试

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from tcs34725_color import TCS34725, html_rgb, html_hex

# ======================================== 全局变量 ============================================

tcs_addr = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:test TCS34725 color recognition sensor")

# 根据硬件修改引脚
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list:list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    if device == 0x29:
        print("I2c hexadecimal address:", hex(device))
        tcs_addr = device

sensor = TCS34725(i2c, tcs_addr)
# 获取并打印传感器 ID
led = Pin(2, Pin.OUT)
sensor_id = sensor.sensor_id()
print(f"Sensor ID: 0x{sensor_id:02X}")
time.sleep(3)
# 激活
print("Testing sensor activation...")
sensor.active(True, led)
print("Sensor activated:", sensor.active())
time.sleep(3)

# 积分时间
print("Testing integration time setting...")
sensor.integration_time(24.0)  # 设置 24ms
print("Integration time set to:", sensor.integration_time(), "ms")
time.sleep(3)

print("Testing gain setting...")
# 设置增益为 4
sensor.gain(4)
print("Gain set to:", sensor.gain(None))
time.sleep(3)

print("Testing threshold setting...")
# 设置阈值  小于100和大于2000，连续五次超范围触发中断
sensor.threshold(cycles=5, min_value=100, max_value=2000)
print("Threshold set. Reading back values...")
print("Threshold (cycles, min, max):", sensor.threshold())
time.sleep(3)

# ========================================  主程序  ============================================

while True:
    try:
        # 数据读取测试
        print("Testing color and lux data reading...")
        data_raw = sensor.read(raw=True)
        print("Raw data (R, G, B, C):", data_raw)
        # 色温和光照强度
        cct, lux = sensor.read(raw=False)
        print(f"Calculated CCT: {cct:.2f} K, Lux: {lux:.2f}")
        time.sleep(3)
        """
        # 中断测试
        print("Testing interrupt clear...")
        print("Interrupt status before clear:", sensor.interrupt())
        sensor.interrupt(False)
        print("Interrupt cleared. Status now:", sensor.interrupt())
        time.sleep(3)
        """
        # HTML RGB / HEX 测试
        print("Testing html_rgb and html_hex conversion...")
        rgb = html_rgb(data_raw)
        hex_color = html_hex(data_raw)
        print("RGB values:", rgb)
        print("HEX string:", hex_color)
        time.sleep(3)
    except Exception as e:
        print(" stopping program...")