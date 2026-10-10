# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/22 14:15
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试MAX44009环境光传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
from max44009 import MAX44009
import time

# ======================================== 全局变量 ============================================

I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100000
MAX44009_ADDR_LIST = (0x4A, 0x4B)
I2C_MUX_ADDR = 0x70
I2C_MUX_CHANNELS = 8
READ_INTERVAL = 1

# ======================================== 功能函数 ============================================

def find_sensor_address(i2c):
    """
    查找MAX44009传感器I2C地址
    Args:
        i2c (I2C): I2C总线对象
    Raises:
        RuntimeError: 未找到传感器
    Notes:
        MAX44009地址由A0引脚决定，可能为0x4A或0x4B
    ==========================================
    Find MAX44009 sensor I2C address.
    Args:
        i2c (I2C): I2C bus object
    Raises:
        RuntimeError: Sensor not found
    Notes:
        MAX44009 address depends on A0 pin, can be 0x4A or 0x4B
    """
    devices = i2c.scan()
    print("Devices: %s" % str([hex(d) for d in devices]))
    for address in MAX44009_ADDR_LIST:
        if address in devices:
            return address
    raise RuntimeError("MAX44009 not found")


def select_mux_channel(i2c, channel):
    """
    选择TCA9548A多路复用器通道
    Args:
        i2c (I2C): I2C总线对象
        channel (int): 多路复用器通道
    Raises:
        ValueError: 通道参数无效
    Notes:
        未使用多路复用器时不需要调用
    ==========================================
    Select TCA9548A multiplexer channel.
    Args:
        i2c (I2C): I2C bus object
        channel (int): Multiplexer channel
    Raises:
        ValueError: Channel parameter is invalid
    Notes:
        Not needed without multiplexer
    """
    if channel < 0 or channel >= I2C_MUX_CHANNELS:
        raise ValueError("Mux channel out of range")
    i2c.writeto(I2C_MUX_ADDR, bytes([1 << channel]))


def find_sensor_with_mux(i2c):
    """
    通过可选多路复用器查找MAX44009传感器
    Args:
        i2c (I2C): I2C总线对象
    Raises:
        RuntimeError: 未找到传感器
    Notes:
        如果总线上存在0x70设备则尝试按TCA9548A处理
    ==========================================
    Find MAX44009 sensor with optional multiplexer.
    Args:
        i2c (I2C): I2C bus object
    Raises:
        RuntimeError: Sensor not found
    Notes:
        If 0x70 exists on bus it is tried as TCA9548A
    """
    devices = i2c.scan()
    for address in MAX44009_ADDR_LIST:
        if address in devices:
            return address, None
    if I2C_MUX_ADDR not in devices:
        raise RuntimeError("MAX44009 not found")
    for channel in range(I2C_MUX_CHANNELS):
        select_mux_channel(i2c, channel)
        time.sleep_ms(10)
        channel_devices = i2c.scan()
        print("Mux channel %d devices: %s" % (channel, str([hex(d) for d in channel_devices])))
        for address in MAX44009_ADDR_LIST:
            if address in channel_devices:
                return address, channel
    i2c.writeto(I2C_MUX_ADDR, bytes([0x00]))
    raise RuntimeError("MAX44009 not found")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using MAX44009 ambient light sensor ...")

# 初始化硬件I2C总线
i2c = I2C(I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 自动查找传感器I2C地址（支持TCA9548A多路复用器）
sensor_address, mux_channel = find_sensor_with_mux(i2c)
print("MAX44009 address: 0x%02X" % sensor_address)
if mux_channel is not None:
    print("MAX44009 mux channel: %d" % mux_channel)

# 初始化传感器对象
sensor = MAX44009(i2c, address=sensor_address)

# 配置传感器参数
sensor.continuous = 1
sensor.manual = 0
sensor.current_division_ratio = 0
sensor.integration_time = 3
print("Configuration register: %d" % sensor._config)

# ========================================  主程序  ===========================================

try:
    while True:
        lux = sensor.lux
        lux_fast = sensor.lux_fast
        int_status = sensor.int_status
        print("Lux: %.2f lx  Fast: %.2f lx  Interrupt: %d" % (lux, lux_fast, int_status))
        time.sleep(READ_INTERVAL)

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
