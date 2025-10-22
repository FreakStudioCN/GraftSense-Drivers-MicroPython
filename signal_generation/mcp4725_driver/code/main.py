# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/1 下午2:10   
# @Author  : 李清水            
# @File    : main.py       
# @Description : DAC类实验，使用外置DAC芯片产生正弦波形

# ======================================== 导入相关模块 ========================================

# 导入硬件模块
from machine import ADC, Timer, Pin, I2C, UART
# 导入时间相关模块
import time
# 导入访问和控制 MicroPython 内部结构的模块
import micropython
# 导入数学库用于计算正弦波
import math
# 导入mcp4725模块用于控制DAC芯片
from mcp4725 import MCP4725

# ======================================== 全局变量 ============================================

# mcp4725芯片地址
DAC_ADDRESS = 0x00
# 电压转换系数
adc_conversion_factor = 3.3 / (65535)

# ======================================== 功能函数 ============================================

# 定时器回调函数
def timer_callback(timer: Timer) -> None:
    """
    定时器回调函数，用于定时读取ADC数据并调用用户自定义的回调函数。

    Args:
        timer (machine.Timer): 定时器实例。

    Returns:
        None
    """

    # 声明全局变量
    global adc,adc_conversion_factor

    # 读取ADC数据
    value = adc.read_u16() * adc_conversion_factor
    # 调用用户自定义的回调函数
    micropython.schedule(user_callback, (value))

# 用户自定义的回调函数
def user_callback(value: float) -> None:
    """
    用户自定义的回调函数，用于处理ADC采集到的电压值并通过串口发送。

    Args:
        value (float): ADC采集到的电压值。

    Returns:
        None
    """
    # 声明全局变量
    global uart

    # 获取浮点数并将其四舍五入到两位小数
    formatted_value = "{:.2f}".format(value)
    # 串口发送采集到的电压数据
    uart.write(str(formatted_value) + '\r\n')
    # 终端打印采集到的电压数据
    print('dac generated voltage: ' + str(formatted_value))

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using DAC to generate sine wave")

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为2，SCL引脚为3
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 便利从机设备地址列表
    for device in devices_list:
        # 如果设备地址在0x60-0x61之间，则为DAC芯片
        if 0x60 <= device <= 0x61:
            print("I2C hexadecimal address: ", hex(device))
            DAC_ADDRESS = device

# 创建DAC对象，使用I2C0外设，地址为DAC_ADDRESS
dac = MCP4725(i2c, DAC_ADDRESS)
# 读取DAC的配置信息
eeprom_write_busy, power_down, value, eeprom_power_down, eeprom_value = dac.read()
print(eeprom_write_busy, power_down, value, eeprom_power_down, eeprom_value)
# 配置DAC：取消电源关断模式，输出电压为0V，写入EEPROM
dac.config(power_down='Off',value=0,eeprom=True)
# 延时50ms，配置完成后立即读取会发生错误
time.sleep_ms(50)
# 读取DAC的配置信息
eeprom_write_busy, power_down, value, eeprom_power_down, eeprom_value = dac.read()
print(eeprom_write_busy, power_down, value, eeprom_power_down, eeprom_value)

# 创建ADC实例：ADC1-GP27
adc = ADC(1)
# 创建软件定时器对象
timer = Timer(-1)
# 启动定时器，每 5ms 触发一次 timer_callback 函数，ADC采集电压
timer.init(period=5, mode=Timer.PERIODIC, callback=timer_callback)

# 创建串口对象，设置波特率为115200
uart = UART(0, 115200)
# 初始化uart对象，波特率为115200，数据位为8，无校验位，停止位为1
# 设置串口超时时间为100ms
uart.init(baudrate  = 115200,
          bits      = 8,
          parity    = None,
          stop      = 1,
          tx        = 0,
          rx        = 1,
          timeout   = 100)

# ========================================  主程序  ===========================================

# 生成正弦波
for i in range(10000):
    # 计算正弦波的电压值
    value = 3.3 * math.sin(2 * math.pi * i / 100) + 3.3
    # 将正弦波的电压值转换为整数
    value = int(value * 4095 / 6.6)
    # DAC写入模拟量
    dac.write(value)
    # 延时10ms
    time.sleep_ms(10)

# 停止ADC采集
timer.deinit()