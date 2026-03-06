# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午2:21
# @Author  : hogeiha
# @File    : main.py
# @Description : MEMS气体传感器多通道读取示例代码，实现VOC/CO/H2S/NO2四种气体的校准和实时浓度读取

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
import time
from mems_air_module import MEMSGasSensor, PCA9546ADR, AirQualityMonitor

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using IIC to read MEMS sensor")

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)


monitor = AirQualityMonitor(i2c)


# 通道0:VOC传感器注册与校准
print("Registering and calibrating VOC sensor on channel 0...")
monitor.register_sensor(0, MEMSGasSensor.TYPE_VOC)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_VOC)

# 通道1:CO传感器注册与校准
print("Registering and calibrating CO sensor on channel 1...")
monitor.register_sensor(1, MEMSGasSensor.TYPE_CO)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_CO)

# 通道2:H2S传感器注册与校准
print("Registering and calibrating H2S sensor on channel 2...")
monitor.register_sensor(2, MEMSGasSensor.TYPE_H2S)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_H2S)

# 通道3:NO2传感器注册与校准
print("Registering and calibrating NO2 sensor on channel 3...")
monitor.register_sensor(3, MEMSGasSensor.TYPE_NO2)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_NO2)

# ======================================== 主程序 =============================

print("\nStart reading gas concentration (press Ctrl+C to stop)...")
print("-" * 50)

while True:
    try:
        # 读取所有已注册传感器的浓度值，返回{传感器类型: 浓度值}字典
        results = monitor.read_all()

        # 格式化打印各气体浓度值
        print(f"VOC concentration: {results[MEMSGasSensor.TYPE_VOC]}")
        print(f"CO concentration: {results[MEMSGasSensor.TYPE_CO]}")
        print(f"H2S concentration: {results[MEMSGasSensor.TYPE_H2S]}")
        print(f"NO2 concentration: {results[MEMSGasSensor.TYPE_NO2]}")
        print("-" * 50)

    except Exception as e:
        # 捕获并打印所有异常，避免程序崩溃
        print(f"Error reading concentration: {str(e)}")
        print("-" * 50)

    # 每隔1秒读取一次数据
    time.sleep(1)
