# Python env   : MicroPython v1.23.0 on Raspberry Pi Pico
# -*- coding: utf-8 -*-        
# @Time    : 2025/1/19 上午10:57   
# @Author  : 李清水            
# @File    : main.py       
# @Description : 总线电机扩展板示例程序

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin, I2C
# 导入时间相关模块
import time
# 导入自定义模块
from pca9685 import PCA9685
# 导入直流电机控制模块
from bus_dc_motor import BusDCMotor

# ======================================== 全局变量 ============================================

# 外置PWM扩展芯片地址
PCA9685_ADDR = 0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Using PCA9685 to control dc motor and step motor")

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

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
        # 判断地址是否在0x40到0x4F之间，如果是，则为PCA9685芯片地址
        if 0x40 <= device <= 0x4F:
            print("PCA9685 I2C hexadecimal address: ", hex(device))
            PCA9685_ADDR = device

# 创建PCA9685实例，使用I2C0外设
pca9685 = PCA9685(i2c, PCA9685_ADDR)
# 创建BusDCMotor实例，使用PCA9685实例，电机数量为4
motor = BusDCMotor(pca9685, 4)

# ========================================  主程序  ===========================================

# # 控制电机1正转，速度为4000，方向为0（前进）
# motor.set_motor_speed(1, 4000, 0)
# # 控制电机2反转，速度为3000，方向为0（前进）
# motor.set_motor_speed(2, 3000, 0)
#
# # 延时10s
# time.sleep(10)
#
# # 停止电机1
# motor.stop_motor(1)
# # 刹车电机2
# motor.break_motor(2)
motor.set_motor_speed(4, 4000, 0)