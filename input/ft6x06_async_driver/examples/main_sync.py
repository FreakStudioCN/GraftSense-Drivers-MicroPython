# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Salvatore Sanfilippo, FreakStudio
# @File    : main.py
# @Description : 测试FT6x06触摸驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time

# 导入硬件相关模块
from machine import I2C, Pin

# 导入 FT6x06 触摸驱动
from ft6x06 import FT6x06

# ======================================== 全局变量 ============================================

# I2C 总线引脚配置
SCL_PIN = 22
SDA_PIN = 21

# 中断引脚配置（可选，None 表示使用轮询模式）
INT_PIN = None

# FT6x06 默认 I2C 从机地址
_FT6X06_ADDR = 0x38

# FocalTech 厂商 ID 寄存器地址和期望值
_VENDOR_ID_REG = 0xA3
_VENDOR_ID_EXPECTED = 0x11

# 芯片 ID 寄存器地址（用于诊断输出，值因具体芯片型号而异）
_CHIP_ID_REG = 0xA8

# 驱动实例预声明
device = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print("FreakStudio: Testing FT6x06 touch controller driver")

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)

# 扫描 I2C 总线上的设备
print("Starting I2C scan...")
devices = i2c.scan()
print("I2C devices found:", [hex(d) for d in devices])

# 若无设备被扫描到，抛出 RuntimeError
if len(devices) == 0:
    raise RuntimeError("No I2C device found on the bus")

# 检查目标设备地址是否存在
found = False
for d in devices:
    if d == _FT6X06_ADDR:
        found = True
        print("FT6x06 device found at address:", hex(d))
        break

# 若未找到目标设备，抛出 RuntimeError
if not found:
    raise RuntimeError("FT6x06 device not found at expected address 0x{:02X}".format(_FT6X06_ADDR))

# 通过 I2C 读取厂商 ID 进行芯片校验
try:
    vendor_id = i2c.readfrom_mem(_FT6X06_ADDR, _VENDOR_ID_REG, 1)[0]
    print("Vendor ID: 0x{:02X} (expected: 0x{:02X})".format(vendor_id, _VENDOR_ID_EXPECTED))
    if vendor_id != _VENDOR_ID_EXPECTED:
        raise RuntimeError("Chip vendor ID mismatch: expected 0x{:02X}, got 0x{:02X}".format(_VENDOR_ID_EXPECTED, vendor_id))
except OSError as e:
    raise RuntimeError("Failed to read vendor ID register") from e

# 读取芯片 ID 用于诊断输出（不同芯片型号 ID 值不同）
try:
    chip_id = i2c.readfrom_mem(_FT6X06_ADDR, _CHIP_ID_REG, 1)[0]
    print("Chip ID: 0x{:02X}".format(chip_id))
except OSError:
    print("Warning: Could not read chip ID register")

# 初始化中断引脚（若配置了）
int_pin = None
if INT_PIN is not None:
    int_pin = Pin(INT_PIN, Pin.IN)

# 创建 FT6x06 驱动实例（使用轮询模式）
device = FT6x06(i2c, address=_FT6X06_ADDR, interrupt_pin=int_pin)
print("FT6x06 driver initialized successfully")

# ========================================  主程序  ============================================

try:
    while True:
        # 读取触摸点数据
        points = device.get_touch_coords()
        # 若有触摸点被检测到，打印数据
        if points:
            print("Touch points:", points)
        # 延时等待下一次轮询
        time.sleep_ms(100)

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
