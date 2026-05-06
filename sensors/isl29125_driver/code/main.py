# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 20:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试ISL29125 RGB颜色传感器驱动，演示颜色读取、模式配置及颜色识别功能
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
from micropython_isl29125 import isl29125
import time

# ======================================== 全局变量 ============================================

# I2C 引脚与频率配置
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100_000

# 目标传感器 I2C 地址列表
TARGET_SENSOR_ADDRS = [0x44]

# 期望的芯片 ID（用于 ID 验证）
EXPECTED_CHIP_ID = 0x7D

# 测量循环延时（毫秒）
MEAS_DELAY_MS = 500

# ======================================== 功能函数 ============================================

def recognize_color(red: int, green: int, blue: int) -> str:
    """
    根据传感器原始 RGB 值识别基础颜色
    Args:
        red (int): 红色原始值，非负整数
        green (int): 绿色原始值，非负整数
        blue (int): 蓝色原始值，非负整数
    Returns:
        str: 颜色名称字符串
    Raises:
        TypeError: 参数类型不是 int
        ValueError: 参数为负数
    Notes:
        采用归一化比例阈值判断，支持 Black/Red/Green/Blue/Yellow/White/Unknown
    ==========================================
    Identify basic color from raw RGB sensor values.
    Args:
        red (int): Raw red value, non-negative integer
        green (int): Raw green value, non-negative integer
        blue (int): Raw blue value, non-negative integer
    Returns:
        str: Color name string
    Raises:
        TypeError: Parameter type is not int
        ValueError: Parameter is negative
    Notes:
        Uses normalized ratio thresholds; supports Black/Red/Green/Blue/Yellow/White/Unknown
    """
    for val, name in ((red, "red"), (green, "green"), (blue, "blue")):
        if not isinstance(val, int):
            raise TypeError("%s must be int, got %s" % (name, type(val).__name__))
        if val < 0:
            raise ValueError("%s cannot be negative, got %d" % (name, val))
    total = red + green + blue
    if total < 50:
        return "Black/No light"
    r_ratio = red / total
    g_ratio = green / total
    b_ratio = blue / total
    if r_ratio > 0.6:
        return "Red"
    elif g_ratio > 0.6:
        return "Green"
    elif b_ratio > 0.6:
        return "Blue"
    elif r_ratio > 0.4 and g_ratio > 0.4:
        return "Yellow"
    elif r_ratio > 0.3 and g_ratio > 0.3 and b_ratio > 0.3:
        return "White"
    return "Unknown"


def test_config(sen) -> None:
    """打印传感器当前配置"""
    print("Operation mode: %s" % sen.operation_mode)
    print("Sensing range: %s" % sen.sensing_range)
    print("ADC resolution: %s" % sen.adc_resolution)
    print(50 * "-")


def test_boundary_values(sen) -> None:
    """
    边界参数测试：验证量程、分辨率、中断阈值极限值设置。

    Args:
        sen: ISL29125传感器实例
    Returns:
        None
    """
    print("--- Boundary value test ---")

    # 测试量程切换边界
    sen.sensing_range = isl29125.LUX_375
    print("sensing_range -> LUX_375: %s" % sen.sensing_range)
    sen.sensing_range = isl29125.LUX_10K
    print("sensing_range -> LUX_10K: %s" % sen.sensing_range)

    # 测试ADC分辨率边界
    sen.adc_resolution = isl29125.RES_12BITS
    print("adc_resolution -> RES_12BITS: %s" % sen.adc_resolution)
    sen.adc_resolution = isl29125.RES_16BITS
    print("adc_resolution -> RES_16BITS: %s" % sen.adc_resolution)

    # 测试中断阈值极限值
    sen.high_threshold = 32767
    sen.low_threshold = 0
    print("high_threshold=32767, low_threshold=0 set OK")

    print("--- Boundary value test passed ---")


def test_exception_values(sen) -> None:
    """
    异常参数测试：验证非法值是否正确抛出异常。

    Args:
        sen: ISL29125传感器实例
    Returns:
        None
    """
    print("--- Exception value test ---")

    # 测试非法工作模式
    try:
        sen.operation_mode = 99
        print("FAIL: should have raised ValueError")
    except ValueError as e:
        print("OK: operation_mode=99 -> ValueError: %s" % str(e))

    # 测试非法量程
    try:
        sen.sensing_range = 99
        print("FAIL: should have raised ValueError")
    except ValueError as e:
        print("OK: sensing_range=99 -> ValueError: %s" % str(e))

    # 测试非法IR补偿值
    try:
        sen.ir_compensation_value = 99
        print("FAIL: should have raised ValueError")
    except ValueError as e:
        print("OK: ir_compensation_value=99 -> ValueError: %s" % str(e))

    # 测试recognize_color非法类型
    try:
        recognize_color("a", 0, 0)
        print("FAIL: should have raised TypeError")
    except TypeError as e:
        print("OK: recognize_color('a',0,0) -> TypeError: %s" % str(e))

    # 测试recognize_color负数参数
    try:
        recognize_color(-1, 0, 0)
        print("FAIL: should have raised ValueError")
    except ValueError as e:
        print("OK: recognize_color(-1,0,0) -> ValueError: %s" % str(e))

    print("--- Exception value test passed ---")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: ISL29125 color sensor test starting ...")

# 初始化 I2C 总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线
devices_list = i2c_bus.scan()
print("I2C scan result: %s" % [hex(d) for d in devices_list])

if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")

# 查找目标传感器地址
sensor = None
for device_addr in devices_list:
    if device_addr in TARGET_SENSOR_ADDRS:
        print("Target sensor found at address: %s" % hex(device_addr))
        sensor = isl29125.ISL29125(i2c=i2c_bus, address=device_addr)
        break

if sensor is None:
    raise RuntimeError("Target sensor not found on I2C bus")

# 验证芯片 ID
chip_id = sensor._device_id
print("Chip ID: %s (expected: %s)" % (hex(chip_id), hex(EXPECTED_CHIP_ID)))
if chip_id != EXPECTED_CHIP_ID:
    raise RuntimeError("Chip ID mismatch: got %s, expected %s" % (hex(chip_id), hex(EXPECTED_CHIP_ID)))

# 配置传感器
sensor.operation_mode = isl29125.RED_GREEN_BLUE
sensor.sensing_range  = isl29125.LUX_10K
sensor.adc_resolution = isl29125.RES_16BITS
sensor.clear_register_flag()
test_config(sensor)

# 执行边界值测试
test_boundary_values(sensor)
print(50 * "-")

# 执行异常参数测试
test_exception_values(sensor)
print(50 * "-")

# ========================================  主程序  ===========================================

try:
    while True:
        # 读取 RGB 三通道原始值
        r, g, b = sensor.colors
        # 识别颜色
        color_name = recognize_color(r, g, b)
        print("R:%5d | G:%5d | B:%5d | Detected: %s" % (r, g, b, color_name))
        time.sleep_ms(MEAS_DELAY_MS)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
