# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/04 10:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : PCA9685  16路PWM驱动板示例程序

# ======================================== 导入相关模块 =========================================

#导入时间模块
import time
# 导入MicroPython标准库模块
from machine import Pin, I2C
# 导入总线舵机控制器模块
from bus_servo import BusPWMServoController
# 导入PCA9685模块
from pca9685 import PCA9685

# ======================================== 全局变量 ============================================

# 自动扫描 PCA9685 地址（0x40~0x4F）
addr = 0x40

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Using PCA9685 to control the angles of two servos")
# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为4，SCL引脚为5
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 遍历从机设备地址列表
    for device in devices_list:
        # 判断设备地址是否为PCF8575的地址
        if device >= 0x40 and device <= 0x4F:
            print("I2C hexadecimal address: ", hex(device))
pca = PCA9685(i2c,  address = device)

# 创建控制器（50Hz 常用于舵机）
srv = BusPWMServoController(pca, freq=50)

# 绑定舵机通道

# 通道0：180° 舵机，标准 500~2500us，1500us 为中立
srv.attach_servo(0, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)
# 通道1：180° 舵机，标准 500~2500us，1500us 为中立
srv.attach_servo(1, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)
# 通道2：180° 舵机，标准 500~2500us，1500us 为中立
srv.attach_servo(2, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)
# 通道3：180° 舵机，标准 500~2500us，1500us 为中立
srv.attach_servo(3, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)

# 设置360°舵机通道
# 通道1：360° 连续舵机，自带停转点在 1500us 附近；如需反向可 reversed=True
srv.attach_servo(4, BusPWMServoController.SERVO_360, min_us=1000, max_us=2000, neutral_us=1500)
# 通道1：360° 连续舵机，自带停转点在 1500us 附近；如需反向可 reversed=True
srv.attach_servo(5, BusPWMServoController.SERVO_360, min_us=1000, max_us=2000, neutral_us=1500)

# ========================================  主程序  ===========================================

# 演示 180° 角度控制
# 转到 0°
srv.set_angle(0, 0.0)
# 转到 0°
srv.set_angle(1, 0.0)
# 转到 0°
srv.set_angle(2, 0.0)
# 转到 0°
srv.set_angle(3, 0.0)
time.sleep(1)
# 以约 120°/s 平滑转到 90°
srv.set_angle(0, 90.0, speed_deg_per_s=120)
# 以约 120°/s 平滑转到 90°
srv.set_angle(1, 90.0, speed_deg_per_s=120)
# 以约 120°/s 平滑转到 90°
srv.set_angle(2, 90.0, speed_deg_per_s=120)
# 以约 120°/s 平滑转到 90°
srv.set_angle(3, 90.0, speed_deg_per_s=120)
time.sleep(1)
# 平滑转到 180°
srv.set_angle(0, 180.0, speed_deg_per_s=180)
# 平滑转到 180°
srv.set_angle(1, 180.0, speed_deg_per_s=180)
# 平滑转到 180°
srv.set_angle(2, 180.0, speed_deg_per_s=180)
# 平滑转到 180°
srv.set_angle(3, 180.0, speed_deg_per_s=180)
time.sleep(1)
# 回中或停
srv.stop(0)

# 演示 360° 速度控制
# 顺时针中速
srv.set_speed(4, +0.6)
# 顺时针中速
srv.set_speed(5, +0.6)
time.sleep(20)
# 反向中速
srv.set_speed(4, -0.6)
# 反向中速
srv.set_speed(5, -0.6)
time.sleep(20)
# 4号通道回中或停
srv.stop(4)
# 5号通道回中或停
srv.stop(5)
# 回中或停

time.sleep(0.5)
# 关闭输出并解除绑定
srv.detach_servo(0)
# 关闭输出并解除绑定
srv.detach_servo(1)
# 关闭输出并解除绑定
srv.detach_servo(2)
# 关闭输出并解除绑定
srv.detach_servo(3)
# 关闭输出并解除绑定
srv.detach_servo(4)
# 关闭输出并解除绑定
srv.detach_servo(5)
