# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午3:30
# @Author  : FreakStudio
# @File    : main.py
# @Description : MLX90393三轴磁力计数据读取示例


# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于延时
import time
# 从machine模块导入引脚控制和I2C类
from machine import Pin, I2C
# 从micropython_mlx90393模块导入MLX90393驱动
from micropython_mlx90393 import mlx90393


# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x0C]  # MLX90393 默认I2C地址


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统稳定
time.sleep(3)
# 打印程序功能提示
print("FreakStudio: MLX90393 Magnetometer Reading")

# I2C初始化（兼容I2C/SoftI2C）
# 使用I2C总线0，SDA引脚GP4，SCL引脚GP5（适用于UM FeatherS2开发板）
i2c_bus = I2C(0, sda=Pin(4), scl=Pin(5))

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
sensor = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = mlx90393.MLX90393(i2c=i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")


# ========================================  主程序  ============================================

# 无限循环读取磁场数据
while True:
    # 获取X、Y、Z轴的磁通密度（单位：微特斯拉）
    magx, magy, magz = sensor.magnetic
    # 打印三轴磁场值
    print(f"X: {magx} uT, Y: {magy} uT, Z: {magz} uT")
    print()
    # 延时1秒
    time.sleep(1)