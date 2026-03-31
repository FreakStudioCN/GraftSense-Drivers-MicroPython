# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午7:30
# @Author  : Embedded Developer
# @File    : main.py
# @Description : LIS3DH加速度传感器测试 读取加速度数据并转换为俯仰角和横滚角

# ======================================== 导入相关模块 =========================================

# 导入LIS3DH传感器驱动模块
import lis3dh

# 导入时间模块用于延时和时间戳获取
import time

# 导入数学模块用于角度计算
import math

# 导入Pin和I2C模块用于硬件通信
from machine import Pin, I2C

# ======================================== 全局变量 ============================================

# 定义I2C SCL引脚编号
I2C_SCL_PIN = 5
# 定义I2C SDA引脚编号
I2C_SDA_PIN = 4
# 定义I2C通信频率
I2C_FREQ = 400000
# 定义LIS3DH传感器目标I2C地址
TARGET_SENSOR_ADDR = 0x19

# 记录上次角度转换的时间戳
last_convert_time = 0
# 角度转换的时间间隔（毫秒）
convert_interval = 100
# 俯仰角（初始值）
pitch = 0
# 横滚角（初始值）
roll = 0

# ======================================== 功能函数 ============================================


def convert_accell_rotation(vec):
    """
    将加速度数据转换为俯仰角(Pitch)和横滚角(Roll)
    Args:
        vec: 包含x、y、z三轴加速度值的列表/元组

    Returns:
        元组，包含当前计算的横滚角和俯仰角（单位：度）

    Notes:
        每100毫秒重新计算一次角度，降低计算频率；角度计算使用反正切函数，转换为角度制
    ==========================================
    Convert acceleration data to Pitch and Roll angles
    Args:
        vec: List/tuple containing x, y, z three-axis acceleration values

    Returns:
        Tuple containing the currently calculated roll angle and pitch angle (unit: degrees)

    Notes:
        Recalculate angles every 100 milliseconds to reduce calculation frequency; angle calculation uses arctangent function and converts to degrees
    """
    x_Buff = vec[0]  # 提取x轴加速度值
    y_Buff = vec[1]  # 提取y轴加速度值
    z_Buff = vec[2]  # 提取z轴加速度值

    global last_convert_time, convert_interval, roll, pitch

    # 判断是否达到角度重新计算的时间间隔
    if last_convert_time < time.ticks_ms():
        last_convert_time = time.ticks_ms() + convert_interval

        # 计算横滚角（Roll），转换为角度制
        roll = math.atan2(y_Buff, z_Buff) * 57.3
        # 计算俯仰角（Pitch），转换为角度制
        pitch = math.atan2((-x_Buff), math.sqrt(y_Buff * y_Buff + z_Buff * z_Buff)) * 57.3

    # 返回当前的横滚角和俯仰角
    return (roll, pitch)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: LIS3DH Accelerometer Test and Angle Calculation")

# 初始化I2C总线，指定引脚和通信频率
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
# 扫描I2C总线上的所有设备，获取设备地址列表
devices_list: list[int] = i2c_bus.scan()
# 打印I2C扫描开始提示
print("START I2C SCANNER")
# 检查是否扫描到I2C设备
if len(devices_list) == 0:
    # 打印无设备提示
    print("No i2c device !")
    # 抛出异常并终止程序
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 打印扫描到的设备数量
    print("i2c devices found:", len(devices_list))
    # 初始化传感器对象为None
    imu = None
    # 遍历扫描到的I2C设备地址
    for device in devices_list:
        # 判断是否匹配目标传感器地址
        if device == TARGET_SENSOR_ADDR:
            # 打印匹配到的传感器十六进制地址
            print("I2c hexadecimal address:", hex(device))
            try:
                # 初始化LIS3DH传感器
                imu = lis3dh.LIS3DH_I2C(i2c=i2c_bus, address=TARGET_SENSOR_ADDR)
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
    if imu is None:
        # 抛出未找到传感器的异常
        raise Exception("No LIS3DH found")

# ========================================  主程序  ============================================

# 检查传感器设备是否正常
if imu.device_check():
    # 设置加速度传感器量程为2G
    imu.range = lis3dh.RANGE_2_G

    # 无限循环读取传感器数据
    while True:
        # 读取三轴加速度值并转换为G值（除以标准重力加速度）
        x, y, z = [value / lis3dh.STANDARD_GRAVITY for value in imu.acceleration]
        # 打印x、y、z轴的G值
        print("x = %0.3f G, y = %0.3f G, z = %0.3f G" % (x, y, z))

        # 调用函数将加速度数据转换为俯仰角和横滚角
        p, r = convert_accell_rotation(imu.acceleration)
        # 打印俯仰角和横滚角
        print("pitch = %0.2f, roll = %0.2f" % (p, r))

        # 延时100毫秒，平衡响应性和资源占用
        time.sleep(0.1)
