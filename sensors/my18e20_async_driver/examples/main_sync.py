# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 15:01
# @Author  : 李清水
# @File    : main.py
# @Description : 测试MY18E20温度传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

# 导入硬件相关的模块
from machine import Pin

# 导入时间相关的模块
import time

# 导入单总线通信相关的模块
from onewire import OneWire

# 导入温度传感器类
from my18e20 import MY18E20

# ======================================== 全局变量 ============================================

# 打印间隔（毫秒）
PRINT_INTERVAL_MS = 500

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 等待设备上电稳定
time.sleep(3)
print("FreakStudio: Using MY18E20 OneWire temperature sensor ...")

# 初始化单总线引脚和传感器对象
ow_pin = OneWire(Pin(6))
sensor = MY18E20(ow_pin)

# 扫描总线上的设备，获取ROM地址列表
roms_list = sensor.scan()
# 打印所有设备的ROM地址
for rom in roms_list:
    print("Detected sensor ROM ID: %s" % str(rom))

# 启动首次温度转换
sensor.convert_temp()

# ========================================  主程序  ===========================================

try:
    while True:
        # 等待转换完成（12位分辨率最长750ms）
        time.sleep_ms(PRINT_INTERVAL_MS)
        # 读取并打印每个传感器的温度
        for rom in roms_list:
            temp = sensor.read_temp(rom)
            print("Sensor %s temperature: %s C" % (str(rom), str(temp)))
        # 启动下一次温度转换
        sensor.convert_temp()

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    del sensor
    del ow_pin
    print("Program exited")
