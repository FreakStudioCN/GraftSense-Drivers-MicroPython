# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 19:01
# @Author  : Matt Trentini
# @File    : main.py
# @Description : TMP1075 温度传感器驱动测试
# @License : MIT

import time
from machine import I2C, Pin

from tmp1075 import TMP1075


# ======================================== 导入相关模块 =========================================
# （已在文件头部导入）
# ======================================== 全局变量 ============================================

# I2C 总线配置常量
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400_000

# TMP1075 设备配置常量
TMP1075_ADDRESS = 0x48
EXPECTED_DEVICE_ID = 0x7500

# 打印间隔（毫秒）
PRINT_INTERVAL_MS = 1000
last_print_time = 0


# ======================================== 功能函数 ============================================


def scan_i2c(i2c):
    """
    扫描 I2C 总线，返回发现的设备地址列表
    Args:
        i2c (I2C): I2C 总线实例
    Returns:
        list: 发现的设备地址列表
    """
    devices = (getattr(i2c, "scan")(),)[0]
    print("I2C devices:", ["0x%02X" % address for address in devices])
    return devices


# ======================================== 自定义类 ============================================
# （使用外部驱动类，本文件无需自定义类）
# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using TMP1075 temperature sensor ...")

# 初始化 I2C 总线
i2c = I2C(
    I2C_ID,
    sda=Pin(SDA_PIN),
    scl=Pin(SCL_PIN),
    freq=I2C_FREQ,
)

# 扫描 I2C 总线，检查是否有设备响应
devices = scan_i2c(i2c)
if not devices:
    raise RuntimeError("No I2C device found on bus")

# 验证目标地址是否有设备
if TMP1075_ADDRESS not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % TMP1075_ADDRESS)

# 实例化 TMP1075 传感器（跳过内部 check，由本文件自行校验 ID）
sensor = TMP1075(i2c, address=TMP1075_ADDRESS, check=False)

# 读取并校验设备 ID
device_id = sensor.device_id()
if device_id == EXPECTED_DEVICE_ID:
    print("Device found: TMP1075 (ID: 0x%04X)" % device_id)
else:
    raise RuntimeError("Device ID mismatch: expected 0x%04X, got 0x%04X" % (EXPECTED_DEVICE_ID, device_id))

# 记录初始时间戳
last_print_time = time.ticks_ms()


# ========================================  主程序  ===========================================
try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()
        # 按设定间隔打印温度数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            print(
                "Temperature: %.4f C / %.4f F"
                % (
                    sensor.temperature_c(),
                    sensor.temperature_f(),
                )
            )
            last_print_time = current_time
        # 短暂休眠，降低 CPU 占用
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
