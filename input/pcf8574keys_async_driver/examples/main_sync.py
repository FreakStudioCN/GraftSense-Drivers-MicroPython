# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 上午11:42
# @Author  : 缪贵成
# @File    : main.py
# @Description : 五向按键测试文件

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time
from pcf8574 import PCF8574
from pcf8574keys import PCF8574Keys, KEYS_MAP

# ======================================== 全局变量 ============================================

# I2C配置
I2C_ID = 0
# 根据实际硬件修改
SCL_PIN = 5
# 根据实际硬件修改
SDA_PIN = 4

PCF8574_ADDR = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio:PCF8574 Five-way Button Test Program")
# 初始化I2C
i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print("START I2C SCANNER")

# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    # 遍历从机设备地址列表
    print("i2c devices found:", len(devices_list))
for device in devices_list:
    # 判断设备地址是否为的PCF8574地址
    if 0x20 <= device <= 0x28:
        # 假设第一个找到的设备是PCF8574地址
        print("I2c hexadecimal address:", hex(device))

        PCF8574_ADDR = device
# 初始化PCF8574
pcf = PCF8574(i2c, PCF8574_ADDR)
# 初始化五向按键
keys = PCF8574Keys(pcf, KEYS_MAP)

# ========================================  主程序  ============================================

while True:
    # 打印当前所有按键状态
    all_states = keys.read_all()
    print(all_states)
    # 查看SW1和SW2按键状态，控制LED灯开关
    if keys.read_key("SW1") == True:
        keys.led_on()
    if keys.read_key("SW2") == True:
        keys.led_off()
    # 100ms刷新一次状态显示
    time.sleep(0.1)
