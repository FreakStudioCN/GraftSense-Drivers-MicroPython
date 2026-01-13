# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/6/24 上午10:32
# @Author  : 李清水
# @File    : main.py
# @Description : IIC获取mpu6050数据，然后通过Print函数打印数据

# ======================================== 导入相关模块 ========================================

# 硬件相关的模块
from machine import Pin, SoftI2C
# 时间相关的模块
import time
# 垃圾回收的模块
import gc
# IMU类模块
from mpu6050 import MPU6050, SimpleComplementaryFilter

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

i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=100000)
# 设置GPIO 25为LED输出引脚，下拉电阻使能
LED = Pin(25, Pin.OUT, Pin.PULL_DOWN)
# 初始化MPU6050
mpu = MPU6050(i2c=i2c)

# 初始化互补滤波器
filter_obj = SimpleComplementaryFilter(alpha=0.98)

print("正在校准，请保持静止...")
filter_obj.calibrate(mpu, samples=50)
print("校准完成")

# ========================================  主程序  ============================================
try:
    while True:
        # 点亮LED灯
        LED.on()
        # 获取角度数据
        pitch, roll = filter_obj.update(mpu)

        # 获取原始数据
        accel = mpu.read_accel_data(g=False)
        gyro = mpu.read_gyro_data()

        # 打印数据
        print(f"Pitch: {pitch:.1f}°, Roll: {roll:.1f}°")
        print(f"Acceleration: X={accel['x']:.2f}, Y={accel['y']:.2f}, Z={accel['z']:.2f} m/s²")
        print(f"Angular velocity: X={gyro['x']:.1f}, Y={gyro['y']:.1f}, Z={gyro['z']:.1f} °/s")
        print("-" * 30)
        # 返回可用堆 RAM 的字节数
        print(" the number of RAM remaining is %d bytes ", gc.mem_free())

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