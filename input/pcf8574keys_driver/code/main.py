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
from pcf8574keys import PCF8574Keys

# ======================================== 全局变量 ============================================

# I2C配置
I2C_ID = 0
# 根据实际硬件修改
SCL_PIN = 17
# 根据实际硬件修改
SDA_PIN = 16
# PCF8574地址，默认0x20
PCF8574_ADDR = 0x20

# 五向按键引脚映射（根据实际接线修改）
KEYS_MAP = {
    'UP': 4,
    'DOWN': 1,
    'LEFT': 2,
    'RIGHT': 0,
    'CENTER': 3
}

# ======================================== 功能函数 ============================================

def key_callback(key_name, state):
    """按键状态变化回调函数"""
    status = "press" if state else "release"
    print(f"key {key_name} {status}")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio:PCF8574 Five-way Button Test Program")
# 初始化I2C
i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)

# 初始化PCF8574
pcf = PCF8574(i2c, PCF8574_ADDR)
try:
    pcf.check()
    print(f"PCF8574 found at address {PCF8574_ADDR:#x}")
except OSError as e:
    print(f"PCF8574 Initialize failed: {e}")
    while True:
        time.sleep(1)

# 初始化五向按键
keys = PCF8574Keys(pcf, KEYS_MAP, key_callback)

# ========================================  主程序  ============================================

try:
    while True:
        # 打印当前所有按键状态
        all_states = keys.read_all()
        print("status:", {k: "press" if v else "release" for k, v in all_states.items()})
        time.sleep(0.5)  # 500ms刷新一次状态显示
except KeyboardInterrupt:
    print("test stop")
finally:
    keys.deinit()
    print("Resource release")
