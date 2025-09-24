# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/4 下午11:14
# @Author  : 缪贵成
# @File    : main.py
# @Description :mlx90640点阵红外温度传感器模块驱动测试文件

# ======================================== 导入相关模块 =========================================

from machine import I2C
import time
from mlx90640 import MLX90640, RefreshRate

# ======================================== 全局变量 ============================================

mlxaddr=None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:Testing the MLX90640 fractional infrared temperature sensor")
# Initialize I2C bus (adjust pins if needed)

i2c = I2C(0, scl=1, sda=0, freq=100000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    if 0x30 <= device <= 0x7A:
        print("I2c hexadecimal address:", hex(device))
        mlxaddr = device

# Initialize MLX90640
try:
    thermal_camera = MLX90640(i2c, mlxaddr)
    print("MLX90640 sensor initialized successfully")
except ValueError as init_error:
    print(f"Sensor initialization failed: {init_error}")
    raise SystemExit(1)
# Show sensor info
print(f"Device serial number: {thermal_camera.serial_number}")
# Set refresh rate
try:
    thermal_camera.refresh_rate = RefreshRate.REFRESH_2_HZ
    print(f"Refresh rate set to {thermal_camera.refresh_rate} Hz")
except ValueError as rate_error:
    print(f"Failed to set refresh rate: {rate_error}")
    raise SystemExit(1)
# 比如测人体时候发射率
thermal_camera.emissivity = 0.92
# Prepare temperature data buffer
temperature_frame = [0.0] * 768

# ========================================  主程序  ============================================

# Main measurement loop
try:
    while True:
        try:
            thermal_camera.get_frame(temperature_frame)
        except RuntimeError as read_error:
            print(f"Frame acquisition failed: {read_error}")
            time.sleep(0.5)
            continue

        # Statistics
        min_temp = min(temperature_frame)
        max_temp = max(temperature_frame)
        avg_temp = sum(temperature_frame) / len(temperature_frame)

        print("\n--- Temperature Statistics ---")
        print(f"Min: {min_temp:.2f} °C | Max: {max_temp:.2f} °C | Avg: {avg_temp:.2f} °C")

        # Print a few pixels (top-left 4*4 area)
        print("--- Sample Pixels (Top-Left 4x4) ---")
        # 打印左上角4*4像素
        for row in range(4):
            row_data = [
                # 这里row*32因为一行是32个像素点，所以这个row*32表示每一行的索引，第0行索引是0
                f"{temperature_frame[row*32 + col]:5.1f}"
                for col in range(4)
            ]
            print(" | ".join(row_data))

        # 等待下一次测量，用刷新率编号加1作为近似值来计算，防止读取数据过快
        time.sleep(1.0 / (thermal_camera.refresh_rate + 1))

except KeyboardInterrupt:
    print("\nProgram terminated by user")
finally:
    print("Testing process completed")
