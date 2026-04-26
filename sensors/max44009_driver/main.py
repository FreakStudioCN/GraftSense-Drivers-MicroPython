# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/22 下午2:15
# @Author  : FreakStudio
# @File    : main.py
# @Description : MAX44009环境光照传感器读取示例


# ======================================== 导入相关模块 =========================================

# 导入MicroPython硬件I2C与引脚控制模块
from machine import I2C, Pin

# 导入MAX44009传感器驱动模块
import max44009

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

# MAX44009可能的I2C地址
MAX44009_ADDR_LIST = (0x4A, 0x4B)

# TCA9548A默认I2C地址
I2C_MUX_ADDR = 0x70

# TCA9548A通道数量
I2C_MUX_CHANNELS = 8

# 数据读取间隔时间
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
    Find MAX44009 sensor I2C address
    Args:
        i2c (I2C): I2C bus object

    Raises:
        RuntimeError: Sensor is not found

    Notes:
        MAX44009 address depends on A0 pin and can be 0x4A or 0x4B
    """
    # 扫描I2C总线设备
    devices = i2c.scan()

    # 打印I2C设备扫描结果
    print("Devices: {}".format([hex(device) for device in devices]))

    # 遍历MAX44009可能地址
    for address in MAX44009_ADDR_LIST:

        # 判断当前地址是否存在
        if address in devices:
            return address

    # 未发现传感器时抛出异常
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
    Select TCA9548A multiplexer channel
    Args:
        i2c (I2C): I2C bus object
        channel (int): Multiplexer channel

    Raises:
        ValueError: Channel parameter is invalid

    Notes:
        This is not needed without multiplexer
    """
    # 验证通道范围
    if channel < 0 or channel >= I2C_MUX_CHANNELS:
        raise ValueError("Mux channel out of range")

    # 写入通道选择位
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
    Find MAX44009 sensor with optional multiplexer
    Args:
        i2c (I2C): I2C bus object

    Raises:
        RuntimeError: Sensor is not found

    Notes:
        If 0x70 exists on bus it is tried as TCA9548A
    """
    # 扫描主I2C总线设备
    devices = i2c.scan()

    # 判断主总线上是否直接存在MAX44009
    for address in MAX44009_ADDR_LIST:
        if address in devices:
            return address, None

    # 判断是否存在TCA9548A多路复用器
    if I2C_MUX_ADDR not in devices:
        raise RuntimeError("MAX44009 not found")

    # 逐个选择多路复用器通道扫描
    for channel in range(I2C_MUX_CHANNELS):

        # 切换到当前多路复用器通道
        select_mux_channel(i2c, channel)

        # 等待通道切换稳定
        time.sleep_ms(10)

        # 扫描当前通道设备
        channel_devices = i2c.scan()

        # 打印当前通道扫描结果
        print(
            "Mux channel {} devices: {}".format(
                channel,
                [hex(device) for device in channel_devices],
            )
        )

        # 判断当前通道是否存在MAX44009
        for address in MAX44009_ADDR_LIST:
            if address in channel_devices:
                return address, channel

    # 未发现传感器时关闭多路复用器全部通道
    i2c.writeto(I2C_MUX_ADDR, bytes([0x00]))

    # 未发现传感器时抛出异常
    raise RuntimeError("MAX44009 not found")


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: MAX44009 light sensor")

# 初始化Pico硬件I2C总线
i2c = I2C(
    I2C_ID,
    sda=Pin(I2C_SDA_PIN),
    scl=Pin(I2C_SCL_PIN),
    freq=I2C_FREQ,
)

# 自动查找传感器I2C地址
sensor_address, mux_channel = find_sensor_with_mux(i2c)

# 打印传感器I2C地址
print("MAX44009 address: 0x{:02X}".format(sensor_address))

# 判断是否通过多路复用器找到传感器
if mux_channel is not None:
    print("MAX44009 mux channel: {}".format(mux_channel))

# 创建MAX44009传感器对象
sensor = max44009.MAX44009(i2c, address=sensor_address)

# 设置连续测量模式
sensor.continuous = 1

# 设置自动量程模式
sensor.manual = 0

# 关闭电流分频模式
sensor.current_division_ratio = 0

# 设置积分时间
sensor.integration_time = 3

# 打印当前配置寄存器值
print("Configuration: {}".format(sensor._config))


# ========================================  主程序  ============================================

# 持续读取光照强度数据
while True:

    # 读取高精度光照强度
    lux = sensor.lux

    # 读取快速光照强度
    lux_fast = sensor.lux_fast

    # 读取中断状态
    int_status = sensor.int_status

    # 打印测量结果
    print(
        "Lux: {:.2f} lx, Fast: {:.2f} lx, Interrupt: {}".format(
            lux,
            lux_fast,
            int_status,
        )
    )

    # 等待下一次读取
    time.sleep(READ_INTERVAL)
