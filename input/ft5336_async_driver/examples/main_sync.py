# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试FT5336触摸驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time

# 导入硬件相关模块
from machine import I2C, Pin

# 导入 FT5336 触摸驱动
from ft5336 import FT5336

# ======================================== 全局变量 ============================================

# I2C 总线引脚配置
SCL_PIN = 22
SDA_PIN = 21

# FT5336 默认 I2C 从机地址
_FT5336_ADDR = 0x38

# FT5336 芯片 ID 寄存器地址和期望值
_CHIP_ID_REG = 0xA8
_CHIP_ID_EXPECTED = 0x79

# 驱动实例预声明
device = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print("FreakStudio: Testing FT5336 touch controller driver")

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
    if d == _FT5336_ADDR:
        found = True
        print("FT5336 device found at address:", hex(d))
        break

# 若未找到目标设备，抛出 RuntimeError
if not found:
    raise RuntimeError("FT5336 device not found at expected address 0x{:02X}".format(_FT5336_ADDR))

# 创建 FT5336 驱动实例
device = FT5336(i2c, address=_FT5336_ADDR, width=320, height=480, verify=True)
print("FT5336 driver initialized successfully")

# ========================================  主程序  ============================================

try:
    while True:
        # 读取触摸点数据
        points = device.touches()
        # 若有触摸点被检测到，打印坐标
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
