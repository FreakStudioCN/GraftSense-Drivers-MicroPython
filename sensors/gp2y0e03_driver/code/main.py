# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/22 下午2:15
# @Author  : FreakStudio
# @File    : main.py
# @Description : GP2Y0E03数字红外测距传感器读取示例


# ======================================== 导入相关模块 =========================================

# 导入MicroPython硬件I2C与引脚控制模块
from machine import I2C, Pin

# 导入GP2Y0E03传感器驱动类
from gp2y0e03 import GP2Y0E03

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# I2C总线编号
I2C_ID = 0

# I2C数据引脚编号
I2C_SDA_PIN = 4

# I2C时钟引脚编号
I2C_SCL_PIN = 5

# I2C通信频率
I2C_FREQ = 100000

# GP2Y0E03默认I2C地址
GP2Y0E03_ADDR = 0x40

# 数据读取间隔时间
READ_INTERVAL = 0.5


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: GP2Y0E03 distance sensor")

# 初始化Pico硬件I2C总线
i2c = I2C(
    I2C_ID,
    sda=Pin(I2C_SDA_PIN),
    scl=Pin(I2C_SCL_PIN),
    freq=I2C_FREQ,
)

# 扫描I2C总线设备
devices = i2c.scan()

# 打印I2C设备扫描结果
print("Devices: {}".format([hex(device) for device in devices]))

# 判断GP2Y0E03是否存在
if GP2Y0E03_ADDR not in devices:
    raise RuntimeError("GP2Y0E03 not found")

# 创建GP2Y0E03传感器对象
sensor = GP2Y0E03(i2c, address=GP2Y0E03_ADDR)

# 打印当前距离量程移位值
print("Shift: {}".format(sensor._shift))


# ========================================  主程序  ============================================

# 持续读取距离数据
while True:

    # 读取原始距离值
    raw = sensor.read(raw=True)

    # 读取厘米距离值
    distance = sensor.read()

    # 打印测量结果
    print("Raw: {}, Distance: {:.2f} cm".format(raw, distance))

    # 等待下一次读取
    time.sleep(READ_INTERVAL)
