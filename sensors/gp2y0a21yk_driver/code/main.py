# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/22 14:15
# @Author  : hogeiha
# @File    : main.py
# @Description : GP2Y0A21YK0F红外测距传感器读取示例
# @License : MIT


# ======================================== 导入相关模块 =========================================

import time
from gp2y0a21yk import GP2Y0A21YK


# ======================================== 全局变量 ============================================

# 传感器模拟输出接入的Pico ADC引脚
DISTANCE_ADC_PIN = 26

# Pico ADC参考电压
ADC_REF_VOLTAGE = 3.3

# 采样平均次数
AVERAGE_COUNT = 5

# 数据读取间隔时间（毫秒）
PRINT_INTERVAL = 500

# 近距离判断阈值（厘米）
CLOSE_THRESHOLD_CM = 20

# 远距离判断阈值（厘米）
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

# 初始化上次打印时间戳
last_print_time = time.ticks_ms()


# ========================================  主程序  ============================================

try:
    while True:

        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 按间隔时间读取并打印传感器数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:

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

            # 更新上次打印时间戳
            last_print_time = current_time

        # 短暂休眠降低CPU占用
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
