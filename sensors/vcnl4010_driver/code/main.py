# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 12:00
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 VCNL4010 驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from vcnl4010 import VCNL4010

# ======================================== 全局变量 ============================================
# I2C 设备验证常量
_DEVICE_ID_REG = 0x81  # WHO_AM_I 寄存器地址
_EXPECTED_DEVICE_ID = 0x21  # VCNL4010 设备 ID 期望值
_DEVICE_I2C_ADDR = 0x13  # VCNL4010 默认 I2C 地址

# 定时打印控制
last_print_time = 0
print_interval = 2000  # 打印间隔（ms）

# ======================================== 功能函数 ============================================

# ======================================== 初始化配置 ==========================================
# 等待设备稳定
time.sleep(3)
print("FreakStudio: VCNL4010 driver class test")

last_print_time = time.ticks_ms()

# 初始化 I2C 总线（根据平台修改引脚号）
# ESP32 常用: sda=Pin(21), scl=Pin(22)
# RP2040 常用: sda=Pin(4), scl=Pin(5)
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
print("I2C initialized: sda=4, scl=5")

# I2C 设备扫描（确认传感器在线）
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C scan result: %s" % [hex(d) for d in devices])

# 验证目标地址是否存在
if _DEVICE_I2C_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % _DEVICE_I2C_ADDR)
print("Device found at 0x%02X" % _DEVICE_I2C_ADDR)

# 创建传感器实例（内部自动验证设备 ID）
try:
    sensor = VCNL4010(i2c)
    print("VCNL4010 initialized successfully")
    # 读取并验证设备 ID
    device_id = i2c.readfrom_mem(_DEVICE_I2C_ADDR, _DEVICE_ID_REG, 1)[0]
    if device_id == _EXPECTED_DEVICE_ID:
        print("Device ID verified: 0x%02X (expected 0x%02X)" % (device_id, _EXPECTED_DEVICE_ID))
    else:
        print("Device ID mismatch: got 0x%02X, expected 0x%02X" % (device_id, _EXPECTED_DEVICE_ID))
except RuntimeError as e:
    print("Device initialization failed: %s" % e)
    raise

# 打印初始配置状态
print("Default config:")
print("  proximity_rate: %s" % sensor.proximity_rate)
print("  irl_led_current: %d" % sensor.irl_led_current)
print("  ambient_light_rate: %s" % sensor.ambient_light_rate)
print("  ambient_light_average: %s" % sensor.ambient_light_average)

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 低频查询：自动执行传感器数据读取
            prox = sensor.proximity
            ambient = sensor.ambient
            print("Proximity: %d, Ambient: %.2f lux" % (prox, ambient))
            last_print_time = current_time

        # Optional manual test snippets:
        # - Proximity rates: set sensor.proximity_rate, read sensor.proximity_rate and sensor.proximity.
        # - Ambient rates: set sensor.ambient_light_rate, read sensor.ambient_light_rate and sensor.ambient.
        # - Ambient averages: set sensor.ambient_light_average, read it back, then read sensor.ambient.
        # - IR LED current boundaries: set sensor.irl_led_current to 1, 20, then restore to 2.
        # - Invalid params: set sensor.proximity_rate to 0xFF or sensor.irl_led_current to 30/0 in try/except.

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
