# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/4/21 下午2:30
# @Author  : hogeiha
# @File    : main.py
# @Description : BMM150磁力计中断模式数据采集程序

# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于延时
import time
# 从machine模块导入引脚和软件I2C类
from machine import Pin, SoftI2C
# 导入BMM150传感器驱动库
from micropython_bmm150 import bmm150

# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x10,0x13]  # BMM150默认I2C地址
# I2C数据线引脚编号
I2C_SDA_PIN = 4
# I2C时钟线引脚编号
I2C_SCL_PIN = 5
# I2C总线通信频率（Hz）
I2C_FREQ = 400000

# ======================================== 功能函数 ============================================

# （无功能函数，保留空区域）

# ======================================== 自定义类 ============================================

# （无自定义类，保留空区域）

# ======================================== 初始化配置 ===========================================

# 等待系统稳定
time.sleep(3)
# 打印启动标识（纯英文）
print("FreakStudio: BMM150 sensor initialization")

# 初始化软件I2C总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

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
bmm = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            bmm = bmm150.BMM150(i2c=i2c_bus,address=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# 使能中断模式
bmm.interrupt_mode = bmm150.INT_ENABLED
# 设置高阈值（单位：微特斯拉）
bmm.high_threshold = 100

# ========================================  主程序  ============================================

# 无限循环读取磁力计数据
while True:
    # 读取磁场强度（x, y, z 单位uT，第四个返回值未使用）
    magx, magy, magz, _ = bmm.measurements
    # 打印三个轴向的磁场值
    print(f"x: {magx}uT, y: {magy}uT, z:{magz}uT")
    # 打印中断状态
    print(bmm.status_interrupt)
    # 打印空行分隔
    print()
    # 延时500ms
    time.sleep(0.5)