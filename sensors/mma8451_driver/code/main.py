# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : hogeiha
# @File    : main.py
# @Description : MMA8451加速度传感器示例程序

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, I2C
from micropython_mma8451 import mma8451

# ======================================== 全局变量 ============================================

# I2C总线编号，RP2040上I2C0对应GPIO4(SDA)/GPIO5(SCL)
I2C_BUS_ID = 0
# I2C时钟线引脚
I2C_SCL_PIN = 5
# I2C数据线引脚
I2C_SDA_PIN = 4
# I2C通信频率，设置为400kHz
I2C_FREQ = 400000
# MMA8451传感器固定I2C地址
TARGET_SENSOR_ADDR = 0x1C

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 系统启动延时，确保外设稳定
time.sleep(3)
print("FreakStudio: MMA8451 sensor initialization")

# 初始化硬件I2C
i2c_bus = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查扫描结果是否为空
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 标志位，记录是否成功初始化传感器
sensor_initialized = False

# 遍历扫描到的所有设备地址
for device in devices_list:
    # 匹配目标传感器地址
    if device == TARGET_SENSOR_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 使用扫描到的地址创建传感器对象
            mma = mma8451.MMA8451(i2c=i2c_bus, address=device)
            print("Target sensor initialization successful")
            sensor_initialized = True
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue

# 若未找到目标传感器，抛出异常终止程序
if not sensor_initialized:
    raise Exception("No TargetSensor found")

# 设置传感器数据输出速率为800Hz
mma.data_rate = mma8451.DATARATE_800HZ

# ========================================  主程序  ============================================

# 无限循环，依次切换数据速率并读取加速度值
while True:
    for data_rate in mma8451.data_rate_values:
        print("Current Data rate setting: ", mma.data_rate)
        # 每个速率下连续读取10次
        for _ in range(10):
            accx, accy, accz = mma.acceleration
            print(f"Acceleration: X={accx:0.1f}m/s^2 y={accy:0.1f}m/s^2 z={accz:0.1f}m/s^2")
            print()
            time.sleep(0.5)
        # 切换到下一个数据速率
        mma.data_rate = data_rate
