# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/08/13 17:45
# @Author  : 缪贵成
# @File    : main.py
# @Description : RCWL9623 超声波模块测试主程序，测试了 GPIO/OneWire/UART/I2C 四种模式

# ======================================== 导入相关模块 =========================================

# 导入硬件模块
from machine import Pin, UART, I2C
# 导入时间相关模块
import time
# 导入超声波相关模块
from rcwl9623 import RCWL9623

# ======================================== 全局变量 ============================================

# I2C 时钟频率 (Hz)，默认 100kHz
I2C_DEFAULT_FREQ = 100_000
# I2C 固定通信地址
I2C_DEFAULT_ADDR = 0x57

# 测试模式:可选 RCWL9623.GPIO_MODE, RCWL9623.ONEWIRE_MODE, RCWL9623.UART_MODE, RCWL9623.I2C_MODE
test_mode = RCWL9623.ONEWIRE_MODE
# 测试间隔时间，单位秒
test_interval = 0.5

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Test RCWL9623 Module")

# 根据不同模式选择引脚/创建通信接口，并实例化 RCWL9623 对象
if test_mode == RCWL9623.GPIO_MODE:
    # GPIO的引脚元组(trig_pin, echo_pin)
    gpio_pins = (5, 4)
    sensor = RCWL9623(mode=RCWL9623.GPIO_MODE, gpio_pins=gpio_pins)
    print("FreakStudio: GPIO Mode")
elif test_mode == RCWL9623.ONEWIRE_MODE:
    onewire_pin = 5
    sensor = RCWL9623(mode=RCWL9623.ONEWIRE_MODE, onewire_pin=onewire_pin)
    print("FreakStudio: OneWire Mode")
elif test_mode == RCWL9623.UART_MODE:
    uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
    sensor = RCWL9623(mode=RCWL9623.UART_MODE, uart=uart)
    print("FreakStudio: UART Mode")
elif test_mode == RCWL9623.I2C_MODE:
    i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=I2C_DEFAULT_FREQ)
    sensor = RCWL9623(mode=RCWL9623.I2C_MODE, i2c=i2c)
    print("FreakStudio: I2C Mode")
else:
    raise ValueError("unknown mode: %s" % test_mode)

# ======================================== 主程序 ===============================================

# 循环测距
print("FreakStudio: Start Test")
try:
    while True:
        # 测距
        distance = sensor.read_distance()
        # 判断测距结果是否有效
        # 注意，该超声波芯片有效测量距离为25CM到700CM，超出范围将返回 None。
        if distance is not None:
            # 打印测距结果
            print("Get Distance: %.2f cm" % distance)
        # 延时
        time.sleep(test_interval)
except KeyboardInterrupt:
    print("FreakStudio: Exit Test")
except Exception as e:
    print("FreakStudio: Error: %s" % e)