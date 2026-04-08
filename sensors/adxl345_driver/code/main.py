# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/14 下午2:30
# @Author  : fanday
# @File    : main.py
# @Description : ADXL345三轴加速度传感器测试 初始化I2C扫描 读取XYZ轴加速度数据
# ======================================== 导入相关模块 =========================================

# 从machine模块导入Pin类，用于控制GPIO引脚
from machine import Pin

# 从machine模块导入I2C类，用于I2C通信
from machine import I2C

# 导入时间模块，用于延时操作
import time

# 导入ustruct模块，用于解析二进制数据
import ustruct

# 从adxl345模块导入adxl345类，这是ADXL345传感器的驱动类
from adxl345 import adxl345

# ======================================== 全局变量 ============================================

# I2C总线编号（使用0号总线）
I2C_BUS_NUM = 0
# ADXL345的SCL引脚连接到GP5
I2C_SCL_PIN = 5
# ADXL345的SDA引脚连接到GP4
I2C_SDA_PIN = 4
# I2C通信频率设置为400KHz
I2C_FREQ = 400000
# ADXL345支持的I2C地址列表（默认地址0x53，若SDO引脚拉高则为0x1D）
TARGET_SENSOR_ADDRS = [0x53, 0x1D]
# 初始化传感器对象为None，后续扫描成功后再赋值
snsr = None
# 创建ADXL345片选引脚对象，设置为输出模式（I2C模式下片选引脚需设为输出）
cs = Pin(22, Pin.OUT)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，等待系统稳定
time.sleep(3)
# 输出初始化开始提示（纯英文短句）
print("FreakStudio: Starting I2C scanner for ADXL345")
# 初始化I2C总线，用于扫描设备（传感器初始化时仍使用原始参数格式）
i2c_bus = I2C(I2C_BUS_NUM, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
# 扫描I2C总线上的所有设备地址，返回地址列表
devices_list: list[int] = i2c_bus.scan()
# 打印扫描开始提示
print("START I2C SCANNER")
# 检查是否扫描到任何设备
if len(devices_list) == 0:
    # 未发现设备时打印提示
    print("No i2c device !")
    # 抛出异常并退出程序
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 输出发现的设备数量
    print("i2c devices found:", len(devices_list))
    # 初始化目标地址变量
    target_addr = None
    # 遍历扫描到的所有设备地址
    for device in devices_list:
        # 如果当前地址属于目标传感器地址列表
        if device in TARGET_SENSOR_ADDRS:
            # 记录目标地址
            target_addr = device
            # 以十六进制格式打印目标地址
            print("I2c hexadecimal address:", hex(device))
            try:
                # 按照adxl345类要求传递参数：总线编号、SCL引脚、SDA引脚、片选引脚
                snsr = adxl345(bus=I2C_BUS_NUM, scl=I2C_SCL_PIN, sda=I2C_SDA_PIN, cs=cs)
                # 传感器初始化成功提示
                print("Target sensor initialization successful")
                # 跳出循环
                break
            except Exception as e:
                # 初始化失败时打印异常信息
                print(f"Sensor Initialization failed: {e}")
                # 继续尝试下一个地址
                continue
    # 如果传感器对象仍然为None（未成功初始化）
    if snsr is None:
        # 抛出明确异常，提示检查接线或地址
        raise Exception("No ADXL345 found, please check wiring or address (0x53/0x1D)!")

# ========================================  主程序  ============================================

# 无限循环读取传感器数据
while True:
    # 读取三轴加速度数据，返回值单位是mg
    x, y, z = snsr.readXYZ()
    # 打印X、Y、Z轴数据（单位：mg）
    print("x:", x, "y:", y, "z:", z, "unit:mg")
    # 延时0.5秒
    time.sleep(0.5)
