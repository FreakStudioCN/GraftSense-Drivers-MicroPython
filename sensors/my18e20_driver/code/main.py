# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 下午3:01
# @Author  : 李清水
# @File    : main.py
# @Description : DS18B20温度类实验，使用单总线通信完成数据交互

# ======================================== 导入相关模块 ========================================

# 导入硬件相关的模块
from machine import Pin

# 导入时间相关的模块
import time

# 导入单总线通信相关的模块
from onewire import OneWire

# 导入温度传感器类
from my18e20 import MY18E20

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using OneWire to read DS18B20 temperature")

# 定义单总线通信引脚
ow_pin = OneWire(Pin(6))
# 定义温度传感器
MY18E20 = MY18E20(ow_pin)

# ========================================  主程序  ===========================================

# 扫描总线上的DS18B20，获取设备地址列表
roms_list = MY18E20.scan()
# 打印设备地址列表
for rom in roms_list:
    print("ds18b20 sensor devices rom id:", rom)
# 让所有挂载在总线上的DS18B20转换温度
MY18E20.convert_temp()

# 循环读取温度
while True:
    time.sleep_ms(500)
    for rom in roms_list:
        # 转换并打印温度
        temp = MY18E20.read_temp(rom)
        # 打印温度
        print("ds18b20 sensor {} devices temp {}".format(rom, temp))
    # 启动温度转换
    MY18E20.convert_temp()
