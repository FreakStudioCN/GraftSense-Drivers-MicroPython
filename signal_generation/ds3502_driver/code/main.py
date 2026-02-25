# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/3/21 下午3:04
# @Author  : 李清水
# @File    : main.py
# @Description : 使用DS3502数字电位器输出任意波形

# ======================================== 导入相关模块 ========================================

# 导入硬件模块
from machine import ADC, Timer, Pin, I2C, UART

# 导入时间相关模块
import time

# 导入访问和控制 MicroPython 内部结构的模块
import micropython

# 导入ds3502模块用于控制数字电位器芯片
from ds3502 import DS3502

# 导入波形生成模块
from dac_waveformgenerator import WaveformGenerator

# ======================================== 全局变量 ============================================

# DS3502芯片地址
DAC_ADDRESS = 0x00
# 电压转换系数
adc_conversion_factor = 3.3 / (65535)

# ======================================== 功能函数 ============================================


def timer_callback(timer: Timer) -> None:
    """
    定时器回调函数，用于定时读取ADC数据并调用用户自定义的回调函数。

    Args:
        timer (machine.Timer): 定时器实例。

    Returns:
        None: 此函数没有返回值。

    Raises:
        None: 此函数不抛出异常。
    """

    # 声明全局变量
    global adc, adc_conversion_factor

    # 读取ADC数据
    value = adc.read_u16() * adc_conversion_factor
    # 调用用户自定义的回调函数
    micropython.schedule(user_callback, (value))


def user_callback(value: float) -> None:
    """
    用户自定义的回调函数，用于处理ADC采集到的电压值并通过串口发送。

    Args:
        value (float): ADC采集到的电压值。

    Returns:
        None: 此函数没有返回值。

    Raises:
        None: 此函数不抛出异常。
    """
    # 声明全局变量
    global uart

    # 获取浮点数并将其四舍五入到两位小数
    formatted_value = "{:.2f}".format(value)
    # 串口发送采集到的电压数据
    uart.write(str(formatted_value) + "\r\n")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using Digital Potentiometer chip DS3502 to generate differential waveform")

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为2，SCL引脚为3
i2c = I2C(id=1, sda=Pin(2), scl=Pin(3), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print("START I2C SCANNER")

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print("i2c devices found:", len(devices_list))
    # 遍历从机设备地址列表
    for device in devices_list:
        # 如果设备地址在0x28-0x2B之间，则为DS3502芯片
        if 0x28 <= device <= 0x2B:
            print("I2C hexadecimal address: ", hex(device))
            DAC_ADDRESS = device

# 创建DS3502对象，使用I2C1外设，地址为DAC_ADDRESS
dac = DS3502(i2c, DAC_ADDRESS)
# 设置DS3502为快速模式（仅写入WR寄存器）
dac.set_mode(1)

# 创建串口对象，设置波特率为115200
uart = UART(0, 115200)
# 初始化uart对象，波特率为115200，数据位为8，无校验位，停止位为1
# 设置串口超时时间为100ms
uart.init(baudrate=115200, bits=8, parity=None, stop=1, tx=0, rx=1, timeout=100)

# 创建ADC实例：ADC2-GP28
adc = ADC(2)
# 创建软件定时器对象
timer = Timer(-1)
# 启动定时器，每 1ms 触发一次 timer_callback 函数，ADC采集电压
timer.init(period=10, mode=Timer.PERIODIC, callback=timer_callback)

# ========================================  主程序  ===========================================

# 生成正弦波
print("FreakStudio : Generate Sine Waveform : 10Hz, 1.5V, 1.5V")
# 初始化波形生成器
wave = WaveformGenerator(dac, frequency=5, amplitude=1.5, offset=1.5, waveform="sine")
# 启动波形生成
wave.start()
# 运行一段时间后停止生成
time.sleep(6)
wave.stop()

# 生成方波
print("FreakStudio : Generate Square Waveform : 10Hz, 1.5V, 1.5V")
# 初始化波形生成器
wave = WaveformGenerator(dac, frequency=5, amplitude=1.5, offset=1.5, waveform="square")
# 启动波形生成
wave.start()
# 运行一段时间后停止生成
time.sleep(6)
wave.stop()

# 生成三角波
print("FreakStudio : Generate Triangle Waveform : 10Hz, 1.5V, 1.5V, 0.8")
# 初始化波形生成器
wave = WaveformGenerator(dac, frequency=5, amplitude=1.5, offset=1.5, waveform="triangle", rise_ratio=0.8)
# 启动波形生成
wave.start()
# 运行一段时间后停止生成
time.sleep(6)
wave.stop()

# 停止ADC采集
timer.deinit()
