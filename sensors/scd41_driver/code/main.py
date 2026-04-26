# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : hogeiha
# @File    : main.py
# @Description : SCD4x二氧化碳传感器数据采集程序

# ======================================== 导入相关模块 =========================================

# 从machine模块导入引脚控制和软I2C类
from machine import Pin, SoftI2C
# 导入SCD4x二氧化碳传感器驱动库
from scd4x import SCD4X
# 导入时间模块，用于延时和间隔控制
import time

# ======================================== 全局变量 ============================================

# 定义目标传感器I2C地址列表（SCD4x默认地址0x62）
TARGET_SENSOR_ADDRS = [0x62]
# 定义I2C数据线引脚号（GP4）
I2C_SDA_PIN = 4
# 定义I2C时钟线引脚号（GP5）
I2C_SCL_PIN = 5
# 定义I2C总线通信频率（100kHz）
I2C_FREQ = 100000

# ======================================== 功能函数 ============================================

# （无功能函数，保留空区域）

# ======================================== 自定义类 ============================================

# （无自定义类，保留空区域）

# ======================================== 初始化配置 ===========================================

# 延时3秒，等待硬件稳定
time.sleep(3)
# 打印调试标识和功能说明
print("FreakStudio: SCD4x sensor init and read")

# 使用软I2C初始化总线，指定引脚和频率
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描I2C总线上所有设备，返回地址列表
devices_list: list[int] = i2c_bus.scan()
# 打印扫描开始标记
print("START I2C SCANNER")

# 判断是否扫描到任何I2C设备
if len(devices_list) == 0:
    # 无设备时打印错误信息并退出程序
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 有设备时打印设备数量
    print("i2c devices found:", len(devices_list))

# 初始化传感器对象占位符
sensor = None
# 遍历扫描到的所有设备地址
for device in devices_list:
    # 检查当前地址是否在目标地址列表中
    if device in TARGET_SENSOR_ADDRS:
        # 打印找到的目标设备十六进制地址
        print("I2c hexadecimal address:", hex(device))
        try:
            # 尝试创建SCD4x传感器对象，传入已初始化的I2C总线
            sensor = SCD4X(i2c_bus=i2c_bus,address=device)
            # 初始化成功提示
            print("Sensor initialization successful")
            # 跳出循环，不再继续遍历
            break
        except Exception as e:
            # 初始化失败时打印异常信息，继续尝试其他地址
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 循环完整结束未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# 打印传感器的唯一序列号（属性访问触发读取）
print("SCD4X Serial Number:", sensor.serial_number)

# 设置传感器工作海拔高度（单位：米）
sensor.altitude = 100
# 设置温度偏移补偿值（单位：摄氏度）
sensor.temperature_offset = 2.0
# 启用自动自校准功能（ASC）
sensor.self_calibration_enabled = True
# 将上述配置持久化保存到传感器非易失存储器
sensor.persist_settings()

# 启动周期性测量模式（默认每5秒更新数据）
sensor.start_periodic_measurement()
# 打印测量启动提示
print("Start measuring...")

# ========================================  主程序  ============================================

try:
    # 主循环，持续读取传感器数据
    while True:
        # 检查是否有新的测量数据就绪
        if sensor.data_ready:
            # 读取二氧化碳浓度（单位：ppm）
            co2 = sensor.CO2
            # 读取温度（单位：摄氏度）
            temp = sensor.temperature
            # 读取相对湿度（单位：百分比）
            humi = sensor.relative_humidity
            # 打印所有测量值
            print(f"CO2: {co2} ppm  Temp: {temp:.2f} °C  RH: {humi:.2f} %")
        # 等待5秒再进行下一次数据检查
        time.sleep(5)
except KeyboardInterrupt:
    # 捕获Ctrl+C中断，停止周期性测量
    sensor.stop_periodic_measurement()
    # 打印停止测量提示
    print("Measurement stopped.")