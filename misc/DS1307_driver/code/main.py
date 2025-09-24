# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : 缪贵成
# @File    : main.py
# @Description : rtc时钟测试  设置时间读取时间 设置pico rtc时间

# ======================================== 导入相关模块 =========================================

from machine import Pin, I2C, RTC
import ds1307
import time

# ======================================== 全局变量 ============================================

DS1307_ADDRESS = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: test ds1307 RTC now")
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list:list[int]=i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    # 遍历从机设备地址列表
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    # 判断设备地址是否为的ds1307地址
    if 0x60 <= device <= 0x70:
        # 假设第一个找到的设备是ds1307地址
        print("I2c hexadecimal address:", hex(device))
        DS1307_ADDRESS = device

ds1307rtc = ds1307.DS1307(i2c, DS1307_ADDRESS)
print("DS1307 attributes:", dir(ds1307rtc))

# ========================================  主程序  ============================================


# 振荡器开关测试
ds1307rtc.disable_oscillator = True
print("disable_oscillator =", ds1307rtc.disable_oscillator)

ds1307rtc.disable_oscillator = False
print("disable_oscillator =", ds1307rtc.disable_oscillator, "\n")

# 读取当前时间
print("Current DS1307 datetime:", ds1307rtc.datetime, "\n")

# 设置时间
# 参数：(year, month, day, hour, minute, second, weekday, None)
ds1307rtc.datetime = (2025, 9, 17, 17, 47, 17, 6)

# 再次读取时间
print("After setting datetime:", ds1307rtc.datetime)

# 等待 3.9 秒再读取
time.sleep(3.9)
print("After 3.9s:", ds1307rtc.datetime, "\n")

# 获取 Pico RTC 格式时间
print("DS1307 datetime formatted for Pico RTC:", ds1307rtc.datetimeRTC, "\n")

# 打印 Pico 内部 RTC 时间
print("Pico internal RTC time:", time.localtime(), "\n")

# 设置 Pico RTC
rtc = RTC()
rtc.datetime(ds1307rtc.datetimeRTC)
print("Pico RTC set from DS1307, now:", time.localtime())
