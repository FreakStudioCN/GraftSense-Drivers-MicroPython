# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午11:25
# @Author  : 缪贵成
# @File    : main.py
# @Description : 基于BMP280的大气压强温湿度传感器模块驱动测试程序

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C
from bmp280_float import BMP280

# ======================================== 全局变量 =============================================

bmp_addr = None

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ============================================

time.sleep(3)
print("FreakStudio:Testing BMP280 pressure, temperature, and humidity sensor")
# 注意：引脚号根据实际硬件修改
i2c = I2C(0, scl=1, sda=0, freq=100000)
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
    if 0x60 <= device <= 0x7A:
        print("I2c hexadecimal address:", hex(device))
        bmp_addr = device

bmp = BMP280(i2c=i2c, address=bmp_addr)

# ======================================== 主程序 ===============================================
try:
    print("FreakStudio: Testing BMP280 sensor (Temperature, Humidity, Pressure)")
    while True:
        # 获取浮点数温湿度和气压
        temp, press, hum = bmp.read_compensated_data()
        # 转换气压单位为 hPa（1 hPa = 100 Pa）
        press_hpa = press / 100.0
        # 计算海拔高度
        sea_level_hpa = 1013.25
        altitude = 44330.0 * (1.0 - (press_hpa / sea_level_hpa) ** 0.1903)
        # 打印浮点信息
        print("Temperature: {:.2f} °C | Humidity: {:.2f}% | Pressure: {:.2f} hPa".format(
            temp, hum, press_hpa
        ))
        print(altitude)
        time.sleep(2)
except KeyboardInterrupt:
    print("\nTest stopped")

