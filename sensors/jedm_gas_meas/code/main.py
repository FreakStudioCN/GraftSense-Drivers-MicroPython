# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午2:21
# @Author  : leeqingshui
# @File    : main.py
# @Description : JED系列MEMS数字传感器模块的测试代码

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time
# 导入硬件相关模块
from machine import SoftI2C, Pin
# 导入自定义驱动类
from jedm_gas_meas import JEDMGasMeas

# ======================================== 全局变量 ============================================

# 传感器目标7位地址
TARGET_SENSOR_ADDR = 0x2A
# 传感器模块地址
SENSOR_ADDRESS = 0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio:Using JED MEMS Digital Sensor to measure gas Concentration")

# 创建软件I2C的实例，使用I2C0外设，时钟频率为100KHz，SDA引脚为4，SCL引脚为5
# 对于该模块来说，I2C最大允许通信速率（100KHz）
i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
# 如果传感器模块没有上拉电阻，需要内部上拉
# i2c = SoftI2C(sda=Pin(4, pull=Pin.PULL_UP), scl=Pin(5, pull=Pin.PULL_UP), freq=100000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 遍历从机设备地址列表
    for device in devices_list:
        print("I2C hexadecimal address: ", hex(device))
        if device == 0x2A:
            SENSOR_ADDRESS = device

# 检查是否找到目标传感器地址
if SENSOR_ADDRESS is None:
    raise ValueError("Target sensor address not found")

# 创建传感器模块实例
mems_gas_sensor = JEDMGasMeas(i2c, SENSOR_ADDRESS)

# 传感器预热30秒
print("Sensor preheating for 30 seconds...")
time.sleep(30)
print("Preheating completed.")

# 校零操作：置于通风空气中，执行校零并判断结果
print("Starting zero calibration...")
calib_success = mems_gas_sensor.calibrate_zero()
if calib_success:
    print("Zero calibration succeeded.")
else:
    print("Error: Zero calibration failed! Program exit.")

# ========================================  主程序  ===========================================

while True:
    try:
        # 获取当前气体浓度
        gas_concentration = mems_gas_sensor.read_concentration()
        print(f"Measure Gas Concentration: {gas_concentration}")
    except Exception as e:
        print(f"Error reading concentration: {e}")
    # 每隔1s测试一次
    time.sleep(1)
