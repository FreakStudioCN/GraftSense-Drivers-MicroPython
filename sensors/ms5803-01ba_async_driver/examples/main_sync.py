# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/14 上午11:00
# @Author  : minyiky
# @File    : main.py
# @Description : MS5803温压传感器测试 初始化传感器 读取原始数据 切换不同单位读取温压数据

# ======================================== 导入相关模块 =========================================

# 导入Pin和I2C模块用于硬件通信
from machine import Pin, I2C

# 导入时间模块用于延时操作
import time

# 导入MS5803传感器驱动类
from ms5803 import MS5803  # 导入原始驱动

# ======================================== 全局变量 ============================================

# 定义I2C SCL引脚编号（适配Raspberry Pi Pico）
I2C_SCL_PIN = 5
# 定义I2C SDA引脚编号（适配Raspberry Pi Pico）
I2C_SDA_PIN = 4
# 定义I2C通信频率
I2C_FREQ = 400000
# MS5803传感器支持的I2C地址列表
TARGET_SENSOR_ADDRS = [0x76, 0x77]
# 声明MS5803传感器对象变量
ms_sensor = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: MS5803 Temperature and Pressure Sensor Test")

# 初始化I2C总线，指定引脚和通信频率
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
# 扫描I2C总线上的所有设备地址
devices_list: list[int] = i2c_bus.scan()
# 打印I2C扫描开始提示
print("START I2C SCANNER")
# 判断是否扫描到I2C设备
if len(devices_list) == 0:
    # 打印无I2C设备提示
    print("No i2c device !")
    # 抛出异常并终止程序
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 打印扫描到的I2C设备数量
    print("i2c devices found:", len(devices_list))
    # 初始化目标地址变量
    target_addr = None
    # 遍历扫描到的I2C设备地址
    for device in devices_list:
        # 判断是否匹配MS5803传感器地址
        if device in TARGET_SENSOR_ADDRS:
            # 记录匹配到的传感器地址
            target_addr = device
            # 打印匹配到的传感器十六进制地址
            print("I2c hexadecimal address:", hex(device))
            try:
                # 初始化MS5803传感器，使用默认参数（OSR=256，摄氏度，帕斯卡）
                ms_sensor = MS5803(i2c_bus, address=target_addr)
                # 打印传感器初始化成功提示
                print("Target sensor initialization successful")
                # 找到目标传感器后退出循环
                break
            except Exception as e:
                # 打印传感器初始化失败信息
                print(f"Sensor Initialization failed: {e}")
                # 继续遍历其他地址
                continue
    # 判断是否成功初始化传感器
    if ms_sensor is None:
        # 抛出未找到MS5803传感器的异常
        raise Exception("No MS5803 found, please check the wiring or address!")

# ========================================  主程序  ============================================

# 重置MS5803传感器，恢复出厂校准参数
print("\n=== Reset Sensor ===")
ms_sensor.reset()
# 重置后延时等待传感器稳定
time.sleep_ms(10)

# 读取传感器原始温压数据
print("\n=== 1. Get Raw Temperature and Pressure Data (Unconverted Units) ===")
raw_temp, raw_pressure = ms_sensor.get_measurements()
# 打印原始温度值
print(f"Raw temperature value: {raw_temp}")
# 打印原始压力值
print(f"Raw pressure value: {raw_pressure}")

# 以摄氏度和帕斯卡为单位读取温压数据
print("\n=== 2. Get Data with Custom Units (Celsius + Pascals) ===")
temp_c, pressure_pa = ms_sensor.get_measurements(temp_units="celcius", pressure_units="pascals")
# 打印摄氏度温度值
print(f"Temperature: {temp_c:.2f} °C")
# 打印帕斯卡压力值
print(f"Pressure: {pressure_pa:.2f} Pa")

# 以华氏度和巴为单位读取温压数据
print("\n=== 3. Switch Units (Fahrenheit + Bar) ===")
temp_f, pressure_bar = ms_sensor.get_measurements(temp_units="fahrenheit", pressure_units="bar")
# 打印华氏度温度值
print(f"Temperature: {temp_f:.2f} °F")
# 打印巴压力值
print(f"Pressure: {pressure_bar:.4f} bar")
