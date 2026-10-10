# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 HTS221 温湿度传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin
from hts221 import HTS221

# ======================================== 全局变量 ============================================
# HTS221 默认 I2C 地址
HTS221_I2C_ADDR = 0x5F
# HTS221 WHO_AM_I 期望值
HTS221_CHIP_ID = 0xBC
# HTS221 WHO_AM_I 寄存器地址
HTS221_WHO_AM_I_REG = 0x0F
# 打印间隔（ms）
PRINT_INTERVAL = 2000
# 上次打印时间戳
last_print_time = 0
hts = None


# ======================================== 功能函数 ============================================
def switch_data_rate():
    """
    切换数据速率到 1 Hz（模式切换，默认注释调用，可 REPL 手动触发）
    Switch data rate to 1 Hz (mode switch, commented by default, can be triggered from REPL).
    """
    hts.data_rate = hts.RATE_1_HZ
    print("Data rate switched to RATE_1_HZ")


def single_measurement():
    """
    单次手动测量（仅在 ONE_SHOT 模式下有效，默认注释调用，可 REPL 手动调用）
    Single manual measurement (only valid in ONE_SHOT mode, commented by default, can be called from REPL).
    """
    hts.take_measurements()
    print("Single measurement triggered")


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 hts221.HTS221

# ======================================== 初始化配置 ==========================================
# 等待硬件就绪
time.sleep(3)
print("FreakStudio: Testing HTS221 temperature and humidity sensor driver")

# 初始化 I2C 总线
# ESP32 示例引脚: scl=Pin(22), sda=Pin(21)
# Raspberry Pi Pico 示例引脚: scl=Pin(5), sda=Pin(4)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 验证目标设备是否存在
if HTS221_I2C_ADDR not in devices:
    raise RuntimeError("HTS221 not found at expected address 0x%02X" % HTS221_I2C_ADDR)
print("HTS221 found at 0x%02X" % HTS221_I2C_ADDR)

# 读取并验证 WHO_AM_I 芯片 ID
chip_id = i2c.readfrom_mem(HTS221_I2C_ADDR, HTS221_WHO_AM_I_REG, 1)[0]
if chip_id != HTS221_CHIP_ID:
    raise RuntimeError("Unexpected HTS221 chip ID: expected 0x%02X, got 0x%02X" % (HTS221_CHIP_ID, chip_id))
print("HTS221 chip ID verified: 0x%02X" % chip_id)

# 创建 HTS221 传感器实例
hts = HTS221(i2c, address=HTS221_I2C_ADDR, debug=False)
print("HTS221 initialized successfully")

# ========================================  主程序  ===========================================
last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取温度值（低频核心 API，保留自动执行）
            temp = hts.temperature
            print("Temperature: %.2f C" % temp)

            # 读取湿度值（低频核心 API，保留自动执行）
            hum = hts.relative_humidity
            print("Humidity: %.2f %%rH" % hum)

            # 打印当前配置状态（低频状态查询，保留自动执行）
            print("Data rate: %s, BDU: %s" % (hts.data_rate, hts.block_data_update))
            print("---")
            last_print_time = current_time

        # switch_data_rate()      # 模式切换，注释默认执行，可 REPL 手动触发
        # single_measurement()    # 单次测量，注释默认执行，可 REPL 手动调用
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    hts.deinit()
    hts = None
    print("Program exited")
