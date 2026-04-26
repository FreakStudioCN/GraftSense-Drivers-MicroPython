# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午6:30
# @Author  : hogeiha
# @File    : main.py
# @Description : TCS3472颜色传感器驱动与测试

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
import tcs3472
import time

# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x29]          

# I2C引脚和频率配置
I2C_SDA_PIN = 4  
I2C_SCL_PIN = 5   
I2C_FREQ = 400000


# ======================================== 功能函数 ============================================

def recognize_color(r, g, b):
    # 判断黑色（亮度极低）
    if r < 30 and g < 30 and b < 30:
        return "Black"
    # 判断白色（RGB全高且均衡）
    elif r > 110 and g > 110 and b > 110:
        return "White"
    # 判断红色：R最大且R>110
    elif r > 110 and r > g and r > b:
        return "Red"
    # 判断绿色：G最大且G>110
    elif g > 110 and g > r and g > b:
        return "Green"
    # 判断蓝色：B最大且B>110
    elif b > 110 and b > r and b > g:
        return "Blue"
    # 判断黄色：R和G都高
    elif r > 110 and g > 110 and b < 90:
        return "Yellow"
    # 其他颜色
    else:
        return "Unknown"

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: TCS3472 color sensor test")

# ========================================  主程序  ============================================

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
sensor = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = tcs3472.tcs3472(i2c_bus, device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# 主循环
print("TCS3472 color sensor initialized successfully!")
while True:
    # 检查传感器数据是否有效
    if sensor.valid():
        # 获取环境光亮度
        light_val = sensor.light()
        # 获取RGB值(0-255)
        r, g, b = sensor.rgb()
        # 识别颜色名称
        color_name = recognize_color(r, g, b)
        
        # 打印结果
        print(f"Light: {light_val:>4} | RGB: ({r:3}, {g:3}, {b:3}) | Color: {color_name}")
    else:
        print("Sensor data invalid!")
    
    # 延时500ms，避免刷屏过快
    time.sleep(0.5)