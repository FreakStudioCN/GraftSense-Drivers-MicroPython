# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 CC1101 sub-GHz SPI 收发器驱动类
# @License : GPL-3.0

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SPI
from cc1101 import CC1101

# ======================================== 全局变量 ============================================

# ==================== SPI 引脚配置（根据实际接线修改） ====================
SPI_CHANNEL = 1
SCK_PIN = 18
MOSI_PIN = 23
MISO_PIN = 19

# ==================== 控制和中断引脚配置（根据实际接线修改） ====================
CS_PIN = 5
GDO0_PIN = 4

# ==================== 测试频率配置 ====================
# 433.92 MHz ISM 频段（请根据当地法规和模块型号调整）
TEST_FREQ_HZ = 433920000

# 全局设备引用（用于 finally 块安全释放）
device = None

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing CC1101 sub-GHz SPI transceiver driver...")

# 初始化 SPI 引脚
print("Initializing SPI pins...")
cs_pin = Pin(CS_PIN, Pin.OUT)
cs_pin.value(1)

print("Initializing GDO0 pin...")
gdo0_pin = Pin(GDO0_PIN, Pin.IN)

# 初始化 SPI 总线
# CC1101 支持 SPI mode 0（polarity=0, phase=0），最高 10MHz
print("Initializing SPI bus (baudrate=4MHz, mode 0)...")
spi = SPI(
    SPI_CHANNEL,
    baudrate=4000000,
    polarity=0,
    phase=0,
    sck=Pin(SCK_PIN),
    mosi=Pin(MOSI_PIN),
    miso=Pin(MISO_PIN),
)

# 初始化 CC1101 驱动实例
print("Initializing CC1101 driver...")
device = CC1101(spi, cs_pin, gdo0=gdo0_pin, debug=True)

# SPI 设备检测：验证芯片身份
print("Verifying CC1101 chip identity...")
part, version = device.verify()
print("CC1101 part=0x%02X version=0x%02X" % (part, version))

# 配置载波频率
# 注意：实际使用前需配置完整的调制解调器寄存器参数和合法的射频设置
device.set_frequency(TEST_FREQ_HZ)
device.idle()

print("CC1101 initialized successfully.")

# ========================================  主程序  ===========================================

try:
    while True:
        # 示例循环：保持设备运行
        # 实际应用中可在此处调用 send_packet() / read_packet() 等方法
        time.sleep_ms(1000)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if device is not None:
        device.deinit()
    device = None
    print("Program exited")
