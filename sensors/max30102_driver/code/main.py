# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/16 18:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : MAX30102 心率与PPG读取+简易心率计算器示例

# ======================================== 导入相关模块 =========================================

# MicroPython内置模块
from machine import I2C, Pin
# 导入时间相关模块
import time
#导入MAX30102驱动模块
from heartratemonitor import MAX30102, MAX30105_PULSE_AMP_MEDIUM , HeartRateMonitor, CircularBuffer

# ======================================== 全局变量 ============================================

# 设置每 2 秒计算一次心率
hr_compute_interval = 2

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Use MAX30102 to read heart rate and temperature.")
# I2C0：SDA=GP4，SCL=GP5，400kHz
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
# 创建传感器实例
sensor = MAX30102(i2c=i2c)
# 基础初始化
sensor.setup_sensor()
# 采样率：400 Hz
sensor_sample_rate = 400
sensor.set_sample_rate(sensor_sample_rate)
# FIFO 平均：8
sensor_fifo_average = 8
sensor.set_fifo_average(sensor_fifo_average)
# LED 电流：中档
sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)
# 预计采集速率：400 / 8 = 50 Hz
actual_acquisition_rate = int(sensor_sample_rate / sensor_fifo_average)  # 实际输出 Hz
# 初始化心率监测器
hr_monitor = HeartRateMonitor(
        # 采样率与传感器一致
        sample_rate=actual_acquisition_rate,
        # 心率计算窗口（约 2–5 s，这里取 3 s）
        window_size=int(actual_acquisition_rate * 3),
    )
# 参考时间
ref_time = time.ticks_ms()

# ========================================  主程序  ===========================================

while True:
        # 轮询 FIFO 是否有新数据；有则写入内部存储
        sensor.check()
        time.sleep(0.5)
        # 存储区是否有可用样本
        if sensor.available():
            # 读取 RED/IR/TEMP通道数据（整数）
            red_reading = sensor.pop_red_from_storage()
            ir_reading = sensor.pop_ir_from_storage()
            temp_reading =sensor.read_temperature()
            print("RED: {}, IR: {},TEMP:{:.2f}".format(red_reading, ir_reading,temp_reading))
            # 使用 IR 样本加入心率计算（肤色不同可换 RED/IR/GREEN）
            hr_monitor.add_sample(ir_reading)


        # 间隔 hr_compute_interval 秒计算一次心率
        if time.ticks_diff(time.ticks_ms(), ref_time) / 1000 > hr_compute_interval:
            heart_rate = hr_monitor.calculate_heart_rate()
            if heart_rate is not None:
                print("Heart Rate: {:.0f} BPM".format(heart_rate))
            else:
                print("Not enough data to calculate heart rate")
            # 重置参考时间
            ref_time = time.ticks_ms()

