# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : 基于PCF8574芯片的八段光条数码管模块

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
#导入pcf8574模块
from pcf8574 import PCF8574
#导入基于PCF8574芯片的八段光条数码管模块
from led_bar import LEDBar
#时间相关模块
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Test PCF8574 Module")
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=100000)
# 初始化 PCF8574，假设地址为 0x20
pcf = PCF8574(i2c, 0x20)

# ========================================  主程序  ===========================================

# 创建 LEDBar 实例
ledbar = LEDBar(pcf)
# 1. 单个 LED 点亮（点亮第 3 个 LED）
ledbar.set_led(2, True)
time.sleep(1)

# 2. 单个 LED 熄灭（关闭第 3 个 LED）
ledbar.set_led(2, False)
time.sleep(1)

# 3. 设置所有 LED（例如点亮前 4 个）
ledbar.set_all(0b00001111)
time.sleep(1)

# 4. 显示 level（例如点亮前 6 个 LED）
ledbar.display_level(6)
time.sleep(1)

# 5. 跑马灯效果
for i in range(8):
    ledbar.set_all(1 << i)
    time.sleep(0.2)

# 6. 全部熄灭
ledbar.clear()
