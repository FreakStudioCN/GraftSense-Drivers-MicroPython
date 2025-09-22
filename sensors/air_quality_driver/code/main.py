# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 15:00
# @Author  : 侯钧瀚
# @File    : mian.py
# @Description : 基于MEMS气体传感器的空气质量监测模块示例程序
# ======================================== 导入相关模块 =========================================

# 导入MicroPython标准库模块
from machine import Pin, I2C
# 导入时间模块
import time
# 导入空气质量监测模块
from air_quality import AirQualityMonitor

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Testing Gas Concentration with MEMS Modules")

# 初始化 I2C 总线
i2c = I2C(1, scl=Pin(22), sda=Pin(21))

# 创建空气质量监测模块实例
monitor = AirQualityMonitor(i2c)

# 注册传感器
monitor.register_sensor('VOC_Sensor', monitor.MEMS_SENSOR_ADDR7, 0, monitor.MEMS_SENSOR_ADDR7)

# ========================================  主程序  ===========================================

# 读取 VOC 气体浓度
concentration = monitor.read_gas('VOC_Sensor')
print(f"VOC 气体浓度: {concentration}")

# 校准传感器
success = monitor.calibrate_gas('VOC_Sensor', 0)
print(f"校准成功: {success}")

# 重启模块
monitor.restart()




