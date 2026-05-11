# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/11 07:39
# @Author  : Andreas Bühl, Kattni Rembor
# @File    : main.py
# @Description : AHT20 温湿度传感器测试程序
# @License : MIT

__version__ = "1.0.0"
__author__ = "Andreas Bühl, Kattni Rembor"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import I2C
import utime
import ahtx0

# ======================================== 全局变量 ============================================

I2C_ID = 1
INTERVAL_MS = 2500

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 初始化 I2C 总线，PB7=SDA，PB6=SCL
i2c = I2C(I2C_ID)
# 创建 AHT20 传感器对象
sensor = ahtx0.AHT20(i2c)

# ========================================  主程序  ===========================================

print("AHT20 sensor test started")

while True:
    try:
        # 读取温度
        temp = sensor.temperature
        # 读取相对湿度
        humi = sensor.relative_humidity
        print("Temperature : %5.1f C" % temp)
        print("  Humidity  : %5.1f %%rH" % humi)
        print("-" * 28)
    except RuntimeError as e:
        print("Sensor runtime error: %s" % e)
    except OSError as e:
        print("Sensor OS error: %s" % e)
    # 等待采样间隔
    utime.sleep_ms(INTERVAL_MS)
