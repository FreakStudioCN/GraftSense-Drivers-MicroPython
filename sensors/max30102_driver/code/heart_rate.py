# Python环境：MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @时间    : 2025/09/16 18:00
# @作者    : n-elia
# @文件    : main.py
# @描述    : MAX30102 心率与PPG数据读取+简易心率计算器示例，参考自：https://github.com/n-elia/MAX30102-MicroPython-driver

# ======================================== 导入相关模块 =========================================

# 导入所需模块
from machine import SoftI2C, Pin
# 导入时间模块
import time
from time import ticks_diff, ticks_us, ticks_ms
#导入MAX30102驱动模块
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
# 导入心率监测器
from heart_rate_monitor import HeartRateMonitor
# 导入环形缓冲区模块
from circular_buffer import CircularBuffer

# ======================================== 全局变量 ============================================

# 设置每2秒计算一次心率
hr_compute_interval = 2

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Use MAX30102 to read heart rate and temperature.")
# I2C：SDA=GP4，SCL=GP5，400kHz
i2c = SoftI2C(
    sda=Pin(4),
    scl=Pin(5),
    freq=400000,
)

# 初始化传感器实例
sensor = MAX30102(i2c=i2c)

if sensor.i2c_address not in i2c.scan():
    print("Sensor not found.")

elif not (sensor.check_part_id()):
    # Check that the targeted sensor is compatible
    print("I2C device ID not corresponding to MAX30102 or MAX30105.")

else:
    print("Sensor connected and recognized.")

# 加载默认配置
print("Setting up sensor with default configuration.", "\n")
sensor.setup_sensor()

# 将采样率设置为400：传感器每秒采集400个样本
sensor_sample_rate = 400
sensor.set_sample_rate(sensor_sample_rate)

# 设置每次读取时平均的样本数量
sensor_fifo_average = 8
sensor.set_fifo_average(sensor_fifo_average)

# 将LED亮度设置为中等值
sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)

# 预期采集速率：400 Hz / 8 = 50 Hz
actual_acquisition_rate = int(sensor_sample_rate / sensor_fifo_average)

# 初始化心率监测器
hr_monitor = HeartRateMonitor(
    # 选择与传感器采集速率匹配的采样率
    sample_rate=actual_acquisition_rate,
    # 选择用于计算心率的有效窗口大小（2-5秒）
    window_size=int(actual_acquisition_rate * 3),
)

# 参考时间
ref_time = ticks_ms()

# ========================================  主程序  ===========================================

while True:
    # 必须持续轮询check()方法，以检查传感器的FIFO队列中是否有新读数。
    # 当有新读数可用时，此函数会将它们存入存储区。
    sensor.check()

    # 检查存储区是否有可用样本
    if sensor.available():
        # 从存储区FIFO中获取读数（整数值）
        red_reading = sensor.pop_red_from_storage()
        ir_reading = sensor.pop_ir_from_storage()

        # 将红外读数添加到心率监测器
        # 注意：根据肤色，使用红光、红外光或绿光LED
        # 可以使心率计算更准确。
        hr_monitor.add_sample(ir_reading)

        # 每隔`hr_compute_interval`秒定期计算心率
        if ticks_diff(ticks_ms(), ref_time) / 1000 > hr_compute_interval:
            # 计算心率
            heart_rate = hr_monitor.calculate_heart_rate()
            if heart_rate is not None:
                print("Heart Rate: {:.0f} BPM".format(heart_rate))
            else:
                print("Not enough data to calculate heart rate")
            # 重置参考时间
            ref_time = ticks_ms()
