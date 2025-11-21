# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/23 下午5:44
# @Author  : 缪贵成
# @File    : main.py
# @Description : 8位IO扩展驱动测试文件

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time
from pcf8574 import PCF8574
from pcf8574_io8 import PCF8574IO8

# ======================================== 全局变量 ============================================

PCF8574_ADDR = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:PCF8574 Five-way Button Test Program")
# 初始化I2C
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    # 遍历从机设备地址列表
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    # 判断设备地址是否为的PCF8574地址
    if 0x20 <= device <= 0x28:
        # 找到的设备是PCF_8574地址
        print("I2c hexadecimal address:", hex(device))
        PCF8574_ADDR = device
# 初始化PCF8574
pcf = PCF8574(i2c, PCF8574_ADDR)
# check if device is present
try:
    if pcf.check():
        print("PCF8574 detected successfully.")
except OSError as e:
    print("Error: PCF8574 not found!", e)
# PCF8574IO8 init
# Example: PORT0=(0,1), PORT1=(1,0), PORT2=(1,1), PORT3=(0,0)
ports_init = {0: (1, 1), 1: (1, 1), 2: (1, 1), 3: (1, 1)}
io8 = PCF8574IO8(pcf, ports_init=ports_init)
print("PCF8574IO8 initialized with default port states:", io8.ports_state())
time.sleep(3)

# ========================================  主程序  ============================================

io8.set_port(1,0)
time.sleep(1)
io8.set_port(1,2)
time.sleep(1)
io8.set_port(1,0)
time.sleep(1)
io8.set_port(1,2)

while True:
    if not io8.get_pin(0):  # 引脚0为低电平时（not 1 → False，not 0 → True）
        io8.set_port(1, 2)  # 端口2设置为值2
        print("Button triggered, set port2 to 1")  # 纠正后的打印
    else:  # 引脚0为高电平时
        io8.set_port(1, 0)  # 端口2设置为值0
