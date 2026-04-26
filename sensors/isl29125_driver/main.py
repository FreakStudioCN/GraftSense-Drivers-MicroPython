# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午8:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : ISL29125颜色传感器颜色识别示例，演示驱动库核心接口
# @License : MIT
__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
from micropython_isl29125 import isl29125
import time

# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x44]          # ISL29125默认I2C地址

# I2C引脚和频率配置（根据你的开发板修改！）
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100000

# ======================================== 功能函数 ============================================

def recognize_color(red: int, green: int, blue: int) -> str:
    """
    根据传感器原始RGB值识别基础颜色
    Args:
        red (int): 红色原始值，非负整数
        green (int): 绿色原始值，非负整数
        blue (int): 蓝色原始值，非负整数

    Raises:
        TypeError: 当参数类型不是int时
        ValueError: 当参数为负数时

    Notes:
        采用归一化比例阈值判断，支持黑色、红、绿、蓝、黄、白、未知

    ==========================================
    Identify basic color based on raw RGB values from sensor
    Args:
        red (int): Raw red value, non-negative integer
        green (int): Raw green value, non-negative integer
        blue (int): Raw blue value, non-negative integer

    Raises:
        TypeError: When parameter type is not int
        ValueError: When parameter is negative

    Notes:
        Use normalized ratio threshold judgment, supports black, red, green, blue, yellow, white, unknown
    """
    # 参数类型验证
    for val, name in [(red, "red"), (green, "green"), (blue, "blue")]:
        if not isinstance(val, int):
            raise TypeError(f"{name} must be int, got {type(val).__name__}")
        if val < 0:
            raise ValueError(f"{name} cannot be negative, got {val}")
    
    total = red + green + blue
    if total < 50:
        return "Black/No light"
    
    r_ratio = red / total
    g_ratio = green / total
    b_ratio = blue / total

    if r_ratio > 0.6:
        return "Red"
    elif g_ratio > 0.6:
        return "Green"
    elif b_ratio > 0.6:
        return "Blue"
    elif r_ratio > 0.4 and g_ratio > 0.4:
        return "Yellow"
    elif r_ratio > 0.3 and g_ratio > 0.3 and b_ratio > 0.3:
        return "White"
    else:
        return "Unknown"

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: ISL29125 color sensor test")

# I2C初始化（兼容I2C/SoftI2C）
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    print("Sensor not found, please check wiring/address!")
    while True:
        pass
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
sensor = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = isl29125.ISL29125(i2c=i2c_bus,address=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            print("Sensor not found, please check wiring/address!")
            while True:
                pass
else:
    # 未找到目标设备，抛出异常（但改为死循环以保持原逻辑）
    print("No target sensor device found in I2C bus")
    print("Sensor not found, please check wiring/address!")
    while True:
        pass
    
# ========================================  主程序  ============================================


# 1. 设置工作模式：全RGB通道连续采集
sensor.operation_mode = isl29125.RED_GREEN_BLUE

# 2. 设置测量量程：10000Lux（高量程）
sensor.sensing_range = isl29125.LUX_10K

# 3. 设置ADC分辨率：16位（高精度）
sensor.adc_resolution = isl29125.RES_16BITS

# 4. 清除传感器标志寄存器
sensor.clear_register_flag()

# 打印当前传感器配置
print(f"Operation mode: {sensor.operation_mode}")
print(f"Sensing range: {sensor.sensing_range}")
print(f"ADC resolution: {sensor.adc_resolution}")
print("-" * 50)

while True:
    # 核心接口：读取RGB三色原始数据
    r, g, b = sensor.colors
    
    # 识别颜色
    color_name = recognize_color(r, g, b)
    
    # 打印数据
    print(f"R:{r:>5} | G:{g:>5} | B:{b:>5} | Detected: {color_name}")
    
    # 延时500ms
    time.sleep_ms(500)