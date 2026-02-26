# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/9/25 上午8:31
# @Author  : 李清水
# @File    : main.py
# @Description : I2C类实验，使用PCF8575芯片控制流水灯

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import I2C, Pin

# 时间相关的模块
import time

# 导入自定义的PCF8575类
from pcf8575 import PCF8575

# ======================================== 全局变量 ============================================

# PCF8575芯片地址
PCF8575_ADDRESS: int = 0
# LED灯的数量
LED_COUNT: int = 8

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: control LED using the PCF8575 I/O expander with I2C")

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c: I2C = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print("START I2C SCANNER")

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print("i2c devices found:", len(devices_list))
    # 遍历从机设备地址列表
    for device in devices_list:
        # 判断设备地址是否为PCF8575的地址
        if device >= 0x20 and device <= 0x27:
            print("I2C hexadecimal address: ", hex(device))
            # 假设第一个找到的设备是PCF8575
            PCF8575_ADDRESS = device

# 创建PCF8575类实例
pcf8575 = PCF8575(i2c, PCF8575_ADDRESS)

# ========================================  主程序  ===========================================

# 循环执行
while True:
    # 将端口状态设置为1，熄灭所有流水灯
    pcf8575.port = 0x00FF
    # 延时0.5秒
    time.sleep(0.5)

    # 控制流水灯效果
    for i in range(LED_COUNT):
        # 设置第i个引脚为低电平，点亮对应的LED
        pcf8575.pin(i, False)
        # 延时0.1秒
        time.sleep(0.2)

        # 读取低八位端口状态
        state: int = pcf8575.port & 0xFF
        # 将状态以二进制形式显示
        print("Lower 8 bits state: {:08b}".format(state))

    # 延时0.5秒
    time.sleep(0.5)
