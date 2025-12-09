# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/7/22 下午2:57   
# @Author  : 李清水            
# @File    : main.py       
# @Description : DHT11温湿度传感器类实验，使用单总线通信完成数据交互

# ======================================== 导入相关模块 ========================================

# 导入硬件相关的模块
from machine import Pin
# 导入时间相关的模块
import time
from dht11 import DHT11

# ======================================== 全局变量 ============================================

# 湿度数据
humidity = 0.0
# 温度数据
temperature = 0.0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print('FreakStudio : Using OneWire to read DHT11 sensor')

# 延时1s，等待DHT11传感器上电完成
time.sleep(1)
# 初始化单总线通信引脚，下拉输出
DHT11_PIN = Pin(6, Pin.OUT, Pin.PULL_UP)
# 初始化DHT11实例
dht11 = DHT11(DHT11_PIN)

# ========================================  主程序  ============================================

while True:
    try:
        # 读取温湿度数据
        dht11.measure()
        # 读取温湿度数据
        temperature = dht11.temperature
        humidity = dht11.humidity
        # 打印温湿度数据
        print("temperature: {}℃, humidity: {}%".format(temperature, humidity))
        # 等待2秒
        time.sleep(2)
    except:
        pass
