# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : robert-hh
# @File    : main.py
# @Description : QMC5883P磁力计传感器数据读取示例，通过I2C通信实时获取缩放后的三轴磁场数据并输出

# ======================================== 导入相关模块 =========================================
import math
from machine import I2C, Pin
import time
from qmc5883p import QMC5883P

# ======================================== 全局变量 ============================================

I2C_SCL_PIN = 5  # SCL引脚号
I2C_SDA_PIN = 4  # SDA引脚号
I2C_FREQ = 400_000  # I2C通信频率
QMC5883P_ADDR = 0x2C  # QMC5883P默认I2C地址（十进制13）

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保QMC5883P传感器完成初始化
time.sleep(3)
print("FreakStudio: QMC5883P magnetometer initialization start")

# 按指定风格初始化I2C总线
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

# 【关键修改4】遍历地址列表初始化目标传感器
qmc5883 = None  # 初始化传感器对象变量
for device in devices_list:
    if device == QMC5883P_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            qmc5883 = QMC5883P(i2c=i2c_bus)
            print("QMC5883P sensor initialization successful")
            break
        except Exception as e:
            print(f"QMC5883P Initialization failed: {e}")
            continue
else:
    raise Exception("No QMC5883P sensor found on I2C bus")

# 打印传感器初始化完成提示信息
print("FreakStudio: QMC5883P magnetometer initialized successfully")

# ========================================  主程序  ============================================
# 无限循环读取磁力计传感器数据
while True:
    # 读取并打印缩放后的三轴磁场数据
    print(qmc5883.read_scaled())
    # 延时300毫秒后继续读取下一组数据
    time.sleep_ms(300)
