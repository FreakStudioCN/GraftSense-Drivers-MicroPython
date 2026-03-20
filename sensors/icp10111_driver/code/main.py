# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/20 下午4:00
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 读取ICP10111传感器的气压和温度数据，并循环切换不同的操作模式

# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于实现延时功能
import time
# 导入machine模块中的Pin和I2C类，用于硬件引脚和I2C通信配置
from machine import Pin, I2C
# 导入micropython_icp10111库中的icp10111模块，用于操作ICP10111传感器
import icp10111

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保传感器完成初始化
time.sleep(3)
# 打印初始化提示信息
print("FreakStudio: Read ICP10111 pressure and temperature data")

# 初始化I2C通信，使用RP2040的4号引脚作为SDA，5号引脚作为SCL
i2c = I2C(0, sda=Pin(4), scl=Pin(5))  # Correct I2C pins for RP2040
# 初始化ICP10111传感器对象，传入I2C通信实例
icp = icp10111.ICP10111(i2c)

# 设置传感器的操作模式为正常模式
icp.operation_mode = icp10111.NORMAL

# ========================================  主程序  ============================================

# 无限循环执行数据读取和模式切换操作
while True:
    # 遍历所有支持的操作模式
    for operation_mode in icp10111.operation_mode_values:
        # 打印当前传感器的操作模式设置
        print("Current Operation mode setting: ", icp.operation_mode)
        # 每个模式下读取10次数据
        for _ in range(10):
            # 获取传感器测量的气压和温度数据
            press, temp = icp.measurements
            # 打印气压数据，保留两位小数
            print(f"Pressure {press:.2f}KPa")
            # 打印温度数据，保留两位小数
            print(f"Temperature {temp:.2f}°C")
            # 打印空行，分隔每次的测量数据
            print()
            # 延时0.5秒后进行下一次测量
            time.sleep(0.5)
        # 将传感器切换到下一个操作模式
        icp.operation_mode = operation_mode