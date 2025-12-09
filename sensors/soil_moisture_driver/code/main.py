# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/22 下午12:49
# @Author  : 缪贵成
# @File    : main.py
# @Description : 电容式土壤湿度传感器测试文件

# ======================================== 导入相关模块 =========================================

import time
from soil_moisture import SoilMoistureSensor

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: SoilMoistureSensor Test Start")
print("Please prepare the sensor for calibration (dry and wet)...")

# 初始化传感器 (例：ADC 引脚 26)
sensor = SoilMoistureSensor(pin=26)
print("Sensor initialized on ADC pin 26")

# Step 1: 校准干燥值
input("Place sensor in DRY air/soil and press Enter...")
dry_value = sensor.calibrate_dry()
print("Calibrated dry value:", dry_value)

# Step 2: 校准湿润值
input("Place sensor in WATER (fully wet) and press Enter...")
wet_value = sensor.calibrate_wet()
print("Calibrated wet value:", wet_value)

# Step 3: 设置校准值
sensor.set_calibration(dry_value, wet_value)
print("Calibration set: dry={}, wet={}".format(dry_value, wet_value))

# ======================================== 主程序 ===============================================

# 循环读取传感器数据
print("\nCalibration completed. Start reading moisture...\n")

try:
    while True:
        raw = sensor.read_raw()
        moisture_percent = sensor.read_moisture()
        level = sensor.get_level()

        print(
            "Raw ADC: {:>5} | Moisture: {:>5.1f}% | Level: {}".format(
                raw, moisture_percent, level
            )
        )
        time.sleep(2)

except KeyboardInterrupt:
    print("\nTest stopped by user.")

print("SoilMoistureSensor Test Completed")