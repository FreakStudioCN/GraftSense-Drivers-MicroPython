# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/16 18:00
# @Author  : 侯钧瀚
# @File    : basic_usage.py
# @Description : MAX30102 温度和PPG数据读取示例

# ======================================== 导入相关模块 =========================================

from machine import SoftI2C, Pin
from time import ticks_diff, ticks_us
import time
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# I2C软件实例
# I2C引脚配置：sda=Pin4, scl=Pin5
i2c = SoftI2C(sda=Pin(4),
              scl=Pin(5),
              freq=400000)  # 快速模式：400kHz，慢速模式：100kHz

# 传感器实例
sensor = MAX30102(i2c=i2c)  # 需要传入一个I2C实例

# 扫描I2C总线以确保传感器已连接
if sensor.i2c_address not in i2c.scan():
    print("Sensor not found.")
elif not (sensor.check_part_id()):
    # 检查目标传感器是否兼容
    print("I2C device ID not corresponding to MAX30102 or MAX30105.")
else:
    print("Sensor connected and recognized.")

# 可以使用setup_sensor()方法一次性设置传感器
# 如果不提供参数，则加载默认配置：
# LED模式：2 (红光 + 红外光)
# ADC范围：16384
# 采样率：400 Hz
# LED功率：最大 (50.0mA - 检测距离约12英寸)
# 平均采样数：8
# 脉冲宽度：411
print("Setting up sensor with default configuration.", '\n')
sensor.setup_sensor()

# 也可以逐个调整配置参数
# 将采样率设置为400：传感器每秒采集400个样本
sensor.set_sample_rate(400)
# 设置每个读数的平均采样数
sensor.set_fifo_average(8)
# 将LED亮度设置为中等值
sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)

time.sleep(1)

# readTemperature()方法允许提取芯片温度（单位：°C）
print("Reading temperature in °C.", '\n')
print(sensor.read_temperature())

# 选择是否计算采集频率
compute_frequency = True

print("Starting data acquisition from RED & IR registers...", '\n')
time.sleep(1)

t_start = ticks_us()  # 采集开始时间
samples_n = 0  # 已采集的样本数

# ========================================  主程序  ===========================================

while True:
    # 必须持续轮询check()方法，以检查传感器的FIFO队列中是否有新的读数
    # 当有新的读数可用时，此函数会将它们放入存储中
    sensor.check()

    # 检查存储中是否包含可用样本
    if sensor.available():
        # 访问存储FIFO并收集读数（整数值）
        red_reading = sensor.pop_red_from_storage()
        ir_reading = sensor.pop_ir_from_storage()

        # 打印采集的数据（以便用Serial Plotter绘制）
        print(red_reading, ",", ir_reading)

        # 计算我们接收数据的实际频率
        if compute_frequency:
            if ticks_diff(ticks_us(), t_start) >= 999999:
                f_HZ = samples_n
                samples_n = 0
                print("acquisition frequency = ", f_HZ)
                t_start = ticks_us()
            else:
                samples_n = samples_n + 1