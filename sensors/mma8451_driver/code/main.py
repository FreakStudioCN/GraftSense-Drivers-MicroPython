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
# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x1C,0x1D]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 系统启动延时，确保外设稳定
time.sleep(3)
print("FreakStudio: MMA8451 sensor initialization")

# I2C初始化（兼容I2C/SoftI2C）
i2c_bus = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
mma = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            mma = mma8451.MMA8451(i2c=i2c_bus, address=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

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