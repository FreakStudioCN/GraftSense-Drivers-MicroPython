# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/17 16:35
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : 串口舵机控制示例
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================
# micropython内部模块
from machine import UART, Pin
# 导入 time 提供延时与时间控制
import time
# 导入串口舵机控制版模块
from serial_servo import SerialServo
# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试消息
print("FreakStudio:  Serial Servo Test ")
# 配置UART串口
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))

# 初始化串口舵机控制类
servo = SerialServo(uart)

while True:
    servo.move_servo_immediate(servo_id=4, angle=0.0, time_ms=1000)
    time.sleep(2)
    angle, time_ms = servo.get_servo_move_immediate(servo_id=4)
    print(f"Servo ID: 4, Angle: {angle}, Time: {time_ms}")
    servo.move_servo_immediate(servo_id=4, angle=90.0, time_ms=1000)
    time.sleep(2)
    # 获取舵机的角度和时间设置
    angle, time_ms = servo.get_servo_move_immediate(servo_id=4)
    print(f"Servo ID: 4, Angle: {angle}, Time: {time_ms}")
