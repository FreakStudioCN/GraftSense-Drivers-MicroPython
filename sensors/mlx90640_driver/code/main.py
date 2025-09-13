# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/4 下午11:14
# @Author  : 缪贵成
# @File    : main.py
# @Description :mlx90640点阵红外温度传感器模块驱动测试文件

# ======================================== 导入相关模块 =========================================

import machine
import time
from mlx90640 import MLX90640, RefreshRate

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:Testing the MLX90640 fractional infrared temperature sensor")
# Initialize I2C bus (adjust pins if needed)
i2c_bus = machine.I2C(0, scl=machine.Pin(13), sda=machine.Pin(12), freq=100000)

# Scan I2C devices
print("Scanning I2C bus...")
devices = i2c_bus.scan()
if not devices:
    print("No I2C devices found. Please check wiring!")
    raise SystemExit(1)
else:
    print(f"Found I2C devices: {[hex(dev) for dev in devices]}")

# Initialize MLX90640
try:
    thermal_camera = MLX90640(i2c_bus)
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

        # Print a few pixels (top-left 4x4 area)
        print("--- Sample Pixels (Top-Left 4x4) ---")
        # 打印左上角4*4像素
        for row in range(4):
            row_data = [
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
