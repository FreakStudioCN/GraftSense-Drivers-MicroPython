# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/1/15 下午3:00
# @Author  : hogeiha
# @File    : main.py
# @Description : MMC5983磁力计连续模式读取并遍历操作模式

# ======================================== 导入相关模块 =========================================

# 导入时间模块用于延时
import time

# 导入MicroPython的引脚和软I2C类
from machine import Pin, SoftI2C

# 导入MMC5983磁力计驱动库
from micropython_mmc5983 import mmc5983

# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x30]

# I2C引脚和频率定义
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 等待3秒让系统稳定
time.sleep(3)
# 打印启动提示信息
print("FreakStudio: MMC5983 sensor continuous mode test")

# I2C初始化（兼容I2C/SoftI2C）
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
# 初始化传感器对象占位符
sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = mmc5983.MMC5983(i2c=i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# 设置传感器为连续测量模式
sensor.operation_mode = mmc5983.CONTINUOUS

# ========================================  主程序  ============================================

# 主循环：遍历所有操作模式并读取磁场数据
while True:
    # 遍历所有可用的操作模式
    for operation_mode in mmc5983.operation_mode_values:
        # 打印当前操作模式设置
        print("Current Operation mode setting: ", sensor.operation_mode)
        # 在当前模式下连续读取10次磁场数据
        for _ in range(10):
            # 读取X、Y、Z三轴磁场强度（微特斯拉）
            magx, magy, magz = sensor.magnetic
            # 打印磁场数值，保留两位小数
            print(f"X: {magx:.2f}uT, Y: {magy:.2f}uT, Z: {magz:.2f}uT")
            # 打印空行分隔
            print()
            # 延时0.5秒
            time.sleep(0.5)
        # 切换到下一个操作模式
        sensor.operation_mode = operation_mode
