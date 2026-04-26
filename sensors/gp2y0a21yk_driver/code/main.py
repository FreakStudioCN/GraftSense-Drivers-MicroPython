# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/22 下午2:15
# @Author  : hogeiha
# @File    : main.py
# @Description : GP2Y0A21YK0F红外测距传感器读取示例


# ======================================== 导入相关模块 =========================================

# 导入时间控制模块
import time

# 导入GP2Y0A21YK0F传感器驱动类
from gp2y0a21yk import GP2Y0A21YK


# ======================================== 全局变量 ============================================

# 传感器模拟输出接入的Pico ADC引脚
DISTANCE_ADC_PIN = 26

# Pico ADC参考电压
ADC_REF_VOLTAGE = 3.3

# 采样平均次数
AVERAGE_COUNT = 5

# 数据读取间隔时间
READ_INTERVAL = 0.5

# 近距离判断阈值
CLOSE_THRESHOLD_CM = 20

# 远距离判断阈值
FAR_THRESHOLD_CM = 40


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: GP2Y0A21YK distance sensor")

# 创建GP2Y0A21YK0F传感器对象
sensor = GP2Y0A21YK(distance_pin=DISTANCE_ADC_PIN)

# 设置ADC参考电压
sensor.set_ref_voltage(ADC_REF_VOLTAGE)

# 设置采样平均次数
sensor.set_averaging(AVERAGE_COUNT)

# 启用传感器读取
sensor.set_enabled(True)


# ========================================  主程序  ============================================

# 持续读取传感器测距数据
while True:

    # 读取ADC原始值
    raw = sensor.get_distance_raw()

    # 读取传感器输出电压
    voltage = sensor.get_distance_volt()

    # 读取估算距离
    distance = sensor.get_distance_centimeter()

    # 打印测量结果
    print(
        "Raw: {}, Voltage: {:.1f} mV, Distance: {} cm".format(
            raw,
            voltage,
            distance,
        )
    )

    # 判断物体是否小于近距离阈值
    if sensor.is_closer(CLOSE_THRESHOLD_CM):
        print("Object is close")

    # 判断物体是否大于远距离阈值
    if sensor.is_farther(FAR_THRESHOLD_CM):
        print("Object is far")

    # 等待下一次读取
    time.sleep(READ_INTERVAL)
