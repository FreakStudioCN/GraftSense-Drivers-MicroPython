# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午
# @Author  : FreakStudio
# @File    : main.py
# @Description : VEML6040 RGBW 颜色传感器读取示例

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
from sensor_pack_2.bus_service import I2cAdapter
from veml6040mod import VEML6040, get_g_max_lux
import time

# ======================================== 全局变量 ============================================

# VEML6040 默认 I2C 地址
TARGET_SENSOR_ADDRS = [0x10]

# I2C 数据线连接到 Pico GPIO4
I2C_SDA_PIN = 4

# I2C 时钟线连接到 Pico GPIO5
I2C_SCL_PIN = 5

# I2C 通信频率设置为 400kHz
I2C_FREQ = 400000

# 积分时间配置为 80ms
INTEGRATION_TIME = 1

# ======================================== 功能函数 ============================================


def get_als_lux(green_channel: int, sensitivity: float) -> float:
    """
    根据绿色通道计算环境光照度。
    Args:
        green_channel (int): 绿色通道原始值。
        sensitivity (float): 当前积分时间对应的灵敏度。

    Raises:
        ValueError: 参数为空或取值非法时抛出。
        TypeError: 参数类型非法时抛出。

    Notes:
        VEML6040 使用绿色通道估算环境光照度。

    ==========================================
    Calculate ambient light lux from green channel.
    Args:
        green_channel (int): Green channel raw value.
        sensitivity (float): Sensitivity for current integration time.

    Raises:
        ValueError: Raised when parameter is None or invalid.
        TypeError: Raised when parameter type is invalid.

    Notes:
        VEML6040 estimates ambient lux from green channel.
    """
    if green_channel is None:
        raise ValueError("Green channel cannot be None")

    if sensitivity is None:
        raise ValueError("Sensitivity cannot be None")

    if not isinstance(green_channel, int):
        raise TypeError("Green channel must be integer")

    if sensitivity < 0:
        raise ValueError("Sensitivity must not be negative")

    return sensitivity * green_channel


def detect_color(red: int, green: int, blue: int, white: int) -> str:
    """
    根据 RGBW 原始通道识别基础颜色。
    Args:
        red (int): 红色通道原始值。
        green (int): 绿色通道原始值。
        blue (int): 蓝色通道原始值。
        white (int): 白光通道原始值。

    Raises:
        ValueError: 参数为空或取值非法时抛出。
        TypeError: 参数类型非法时抛出。

    Notes:
        该算法用于基础颜色判断，实际项目可按光源和外壳校准阈值。

    ==========================================
    Detect basic color from RGBW raw channels.
    Args:
        red (int): Red channel raw value.
        green (int): Green channel raw value.
        blue (int): Blue channel raw value.
        white (int): White channel raw value.

    Raises:
        ValueError: Raised when parameter is None or invalid.
        TypeError: Raised when parameter type is invalid.

    Notes:
        This algorithm is for basic color detection and can be calibrated.
    """
    channels = (red, green, blue, white)

    for value in channels:
        if value is None:
            raise ValueError("Color channel cannot be None")

        if not isinstance(value, int):
            raise TypeError("Color channel must be integer")

        if value < 0:
            raise ValueError("Color channel must not be negative")

    rgb_max = max(red, green, blue)
    rgb_min = min(red, green, blue)
    rgb_sum = red + green + blue

    if white < 20 or rgb_max < 10:
        return "Black"

    if rgb_sum == 0:
        return "Black"

    balance = rgb_max - rgb_min

    if balance < rgb_max * 0.18:
        if white > rgb_max * 1.2:
            return "White"

        return "Gray"

    red_ratio = red / rgb_sum
    green_ratio = green / rgb_sum
    blue_ratio = blue / rgb_sum

    if red_ratio > 0.45 and green_ratio > 0.35:
        return "Yellow"

    if green_ratio > 0.42 and blue_ratio > 0.32:
        return "Cyan"

    if red_ratio > 0.42 and blue_ratio > 0.32:
        return "Magenta"

    if red_ratio > green_ratio and red_ratio > blue_ratio:
        return "Red"

    if green_ratio > red_ratio and green_ratio > blue_ratio:
        return "Green"

    if blue_ratio > red_ratio and blue_ratio > green_ratio:
        return "Blue"

    return "Unknown"


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: VEML6040 RGBW color sensor")

# 初始化 I2C 总线
i2c_bus = I2C(id=0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")

# 判断是否扫描到 I2C 设备
if len(devices_list) == 0:
    print("No i2c device")
    raise SystemExit("I2C scan found no devices")

# 判断是否扫描到 VEML6040 默认地址
if TARGET_SENSOR_ADDRS[0] not in devices_list:
    print("VEML6040 address not found")
    raise SystemExit("No VEML6040 device found")

# 打印 VEML6040 地址
print("I2C hexadecimal address:", hex(TARGET_SENSOR_ADDRS[0]))

# 创建 I2C 适配器
adapter = I2cAdapter(i2c_bus)

# 创建 VEML6040 传感器对象
sensor = VEML6040(adapter)

# 确保传感器处于工作状态
if sensor.shutdown:
    sensor.shutdown = False

# 启动单次测量模式
sensor.start_measurement(integr_time=INTEGRATION_TIME, auto_mode=False)

# 获取测量等待时间
wait_time_ms = sensor.get_conversion_cycle_time()

# 获取当前积分时间对应的光照灵敏度
green_sensitivity, max_lux = get_g_max_lux(sensor.integration_time)

# 打印初始化信息
print("Sensor initialization successful")
print("Integration time:", sensor.integration_time)
print("Wait time ms:", wait_time_ms)
print("Green sensitivity:", green_sensitivity)
print("Max detectable lux:", max_lux)

# ========================================  主程序  ============================================

try:
    while True:
        # 等待单次测量完成
        time.sleep_ms(wait_time_ms)

        # 读取 RGBW 原始通道
        red, green, blue, white = sensor.get_colors()

        # 根据绿色通道计算 lux
        lux = get_als_lux(green, green_sensitivity)

        # 根据 RGBW 原始通道识别颜色
        color_name = detect_color(red, green, blue, white)

        # 打印英文格式的颜色和光照数据
        print(
            "Red: {}  Green: {}  Blue: {}  White: {}  Lux: {:.2f}  Color: {}".format(
                red,
                green,
                blue,
                white,
                lux,
                color_name,
            )
        )

        # 再次启动单次测量
        sensor.start_measurement(integr_time=INTEGRATION_TIME, auto_mode=False)
except KeyboardInterrupt:
    # 关闭传感器
    sensor.shutdown = True

    # 打印停止提示
    print("Measurement stopped")
