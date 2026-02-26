# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/6/24 上午10:32
# @Author  : 李清水
# @File    : main.py
# @Description : 串口IMU类实验,主要通过串口获取IMU:JY61数据，然后通过Print函数打印数据

# ======================================== 导入相关模块 ========================================

# 硬件相关的模块
from machine import UART, Pin

# 时间相关的模块
import time

# 垃圾回收的模块
import gc

# IMU类模块
from imu import IMU

# ======================================== 全局变量 ============================================

# 程序运行时间变量
run_time: int = 0
# 程序起始时间点变量
start_time: int = 0
# 程序结束时间点变量
end_time: int = 0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using UART to communicate with IMU")

# 创建串口对象，设置波特率为115200
uart = UART(1, 115200)
# 初始化uart对象，数据位为8，无校验位，停止位为1
# 设置串口超时时间为5ms
uart.init(bits=8, parity=None, stop=1, tx=8, rx=9, timeout=5)

# 创建串口对象，设置波特率为115200，用于将三轴角度数据发送到上位机
uart_pc = UART(0, 115200)
# 初始化uart对象，数据位为8，无校验位，停止位为1，设置串口超时时间为5ms
uart_pc.init(bits=8, parity=None, stop=1, tx=0, rx=1, timeout=5)

# 设置GPIO 25为LED输出引脚，下拉电阻使能
LED = Pin(25, Pin.OUT, Pin.PULL_DOWN)

# 初始化一个IMU对象
imu_obj = IMU(uart)

# ========================================  主程序  ============================================
try:
    while True:
        # 点亮LED灯
        LED.on()
        # 接收陀螺仪数据
        imu_obj.RecvData()
        # 熄灭LED灯
        LED.off()

        # 打印 x 轴角度
        print(" X-axis angle : ", imu_obj.angle_x)
        # 打印 y 轴角度
        print(" Y-axis angle : ", imu_obj.angle_y)
        # 打印 z 轴角度
        print(" Z-axis angle : ", imu_obj.angle_z)
        # 返回可用堆 RAM 的字节数
        print(" the number of RAM remaining is %d bytes ", gc.mem_free())

        # 将三轴角度数据格式化成字符串
        angle_data = "{:.2f}, {:.2f}, {:.2f}\r\n".format(imu_obj.angle_x, imu_obj.angle_y, imu_obj.angle_z)
        # 通过串口0发送角度数据到上位机
        uart_pc.write(angle_data)

        # 当可用堆 RAM 的字节数小于 80000 时，手动触发垃圾回收功能
        if gc.mem_free() < 220000:
            # 手动触发垃圾回收功能
            gc.collect()

except KeyboardInterrupt:
    # 捕获键盘中断（Ctrl+C）时的处理
    print("The program was interrupted by the user")
finally:
    # 无论程序正常结束还是被中断，最终都会执行这里，确保LED关闭
    LED.off()
    print("The LED is off, and the program has exited.")
