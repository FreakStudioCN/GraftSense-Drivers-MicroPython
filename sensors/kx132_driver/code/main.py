# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/23 下午4:23
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 读取KX132加速度传感器的三轴加速度数据并实时打印

# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于实现延时功能
import time

# 导入Pin和I2C模块，用于硬件引脚和I2C通信配置
from machine import Pin, I2C

# 导入kx132模块，用于操作KX132加速度传感器
from micropython_kx132 import kx132

# ======================================== 全局变量 ============================================

# 定义I2C通信常量（适配Raspberry Pi Pico）
I2C_SCL_PIN = 5  # I2C时钟引脚
I2C_SDA_PIN = 4  # I2C数据引脚
I2C_FREQ = 400000  # I2C通信频率（400KHz，KX132支持）
TARGET_SENSOR_ADDR = 0x1F  # KX132加速度传感器默认I2C地址（也可根据硬件配置改为0x1E）
kx = None  # 传感器对象初始化为None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 系统启动延时3秒，确保传感器完成初始化
time.sleep(3)
# 打印初始化完成提示信息
print("FreakStudio: Read KX132 acceleration data")

# 初始化I2C总线（严格对齐指定风格）
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
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
for device in devices_list:
    if device == TARGET_SENSOR_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            kx = kx132.KX132(i2c=i2c_bus)
            print("Target sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    raise Exception("No KX132 sensor found")


# ========================================  主程序  ============================================

# 无限循环读取并打印加速度数据
while True:
    # 读取传感器的三轴加速度数据（x、y、z轴）
    accx, accy, accz = kx.acceleration
    # 格式化打印三轴加速度数据，保留两位小数，单位为g
    print(f"x:{accx:.2f}g, y:{accy:.2f}g, z:{accz:.2f}g")
    # 打印空行，优化输出格式
    print()
    # 延时0.1秒，控制数据打印频率
    time.sleep(0.1)
