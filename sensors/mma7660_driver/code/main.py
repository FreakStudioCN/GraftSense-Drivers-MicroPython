# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/20 下午5:30
# @Author  : Developer
# @File    : main.py
# @Description : 基于Raspberry Pi Pico的MMA7660三轴加速度传感器数据读取程序，实现I2C通信、设备扫描、传感器初始化和加速度数据循环读取

# ======================================== 导入相关模块 =========================================

# 导入I2C和Pin模块，用于硬件I2C通信
from machine import I2C, Pin

# 导入sleep模块，用于程序延时
from time import sleep

# 导入MMA7660加速度传感器驱动类
from mma7660 import Accelerometer

# ======================================== 全局变量 ============================================

# 定义I2C通信的SCL引脚编号（对应Raspberry Pi Pico的GP5）
I2C_SCL_PIN = 5
# 定义I2C通信的SDA引脚编号（对应Raspberry Pi Pico的GP4）
I2C_SDA_PIN = 4
# 定义I2C通信频率（400kHz为Pico常用频率）
I2C_FREQ = 400000
# 定义MMA7660加速度传感器的目标I2C地址
TARGET_SENSOR_ADDR = 0x4C

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 程序启动后延时3秒，确保硬件稳定
sleep(3)
# 打印程序启动提示信息
print("FreakStudio: MMA7660 accelerometer data reading program started")

# 初始化I2C总线0，配置SCL、SDA引脚和通信频率
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描I2C总线上的所有设备，返回设备地址列表并添加类型注解
devices_list: list[int] = i2c_bus.scan()
# 打印I2C扫描启动提示
print("START I2C SCANNER")

# 检查I2C设备扫描结果，若未扫描到任何设备则退出程序
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 打印扫描到的I2C设备数量
    print("i2c devices found:", len(devices_list))

# 初始化传感器变量为None，用于后续接收传感器实例
accel = None
# 遍历扫描到的I2C设备地址列表，查找目标传感器地址
for device in devices_list:
    # 判断当前设备地址是否为MMA7660的目标地址
    if device == TARGET_SENSOR_ADDR:
        # 打印找到的目标传感器十六进制地址
        print("I2c hexadecimal address:", hex(device))
        try:
            # 初始化MMA7660加速度传感器
            accel = Accelerometer(i2c=i2c_bus)
            # 打印传感器初始化成功提示
            print("Target sensor initialization successful")
            # 找到并初始化成功后退出循环
            break
        except Exception as e:
            # 打印传感器初始化失败的异常信息
            print(f"Sensor Initialization failed: {e}")
            # 继续遍历下一个设备地址
            continue
else:
    # 遍历完所有地址未找到目标传感器，抛出异常
    raise Exception("No MMA7660 Accelerometer found on I2C bus")

# ========================================  主程序  ============================================

# 无限循环读取加速度传感器数据
while True:
    # 读取X/Y/Z轴的加速度值（单位：g）
    x_g, y_g, z_g = accel.getXYZ()
    # 读取X/Y/Z轴的加速度值（单位：m/s²）
    x, y, z = accel.getAcceleration()

    # 打印加速度值（单位：g），保留两位小数
    print(f"Acceleration(g): X={x_g:.2f}, Y={y_g:.2f}, Z={z_g:.2f}")
    # 打印加速度值（单位：m/s²），保留两位小数
    print(f"Acceleration(m/s²): X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
    # 打印分隔线，提升输出可读性
    print("-" * 30)
    # 延时0.5秒后继续读取数据
    sleep(0.5)
