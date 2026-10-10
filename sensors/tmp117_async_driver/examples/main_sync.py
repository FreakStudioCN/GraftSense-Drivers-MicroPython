# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 TMP117 高精度数字温度传感器驱动类
# @License : MIT

# ==================== 导入相关模块 ====================

import time
from machine import Pin, I2C
from micropython_tmp117.tmp117 import TMP117

# ==================== 全局变量 ====================

# --- I2C 引脚配置（请根据实际硬件修改）---
I2C_BUS_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000

# --- TMP117 设备参数 ---
TMP117_I2C_ADDR = 0x48
TMP117_CHIP_ID = 0x0117
_TMP117_REG_WHOAMI = 0x0F

# --- 打印间隔 ---
last_print_time = 0
PRINT_INTERVAL_MS = 2000

# ==================== 功能函数 ====================

# ==================== 自定义类 ====================

# (本测试文件无自定义类)

# ==================== 初始化配置 ====================

# 等待硬件上电稳定
time.sleep(3)

print("FreakStudio: TMP117 Driver Test")
print("=" * 50)

# 初始化 I2C 总线
i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
print("I2C initialized: SCL=GPIO%d, SDA=GPIO%d, Freq=%d Hz" % (I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ))

# I2C 总线扫描
devices = i2c.scan()
if not devices:
    print("Warning: No I2C devices found on bus")
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found at:", [hex(addr) for addr in devices])
if TMP117_I2C_ADDR not in devices:
    message = "TMP117 not found at expected address 0x%02X" % TMP117_I2C_ADDR
    raise RuntimeError(message)
print("TMP117 found at expected address 0x%02X" % TMP117_I2C_ADDR)

# 验证芯片 ID
try:
    # 读取 WHO_AM_I 寄存器（2 字节，大端序）
    raw = i2c.readfrom_mem(TMP117_I2C_ADDR, _TMP117_REG_WHOAMI, 2)
    chip_id = (raw[0] << 8) | raw[1]
except OSError as error:
    print("Failed to read device ID: %s" % str(error))
    raise RuntimeError("Device ID verification failed") from error
if chip_id == TMP117_CHIP_ID:
    print("Device verified: TMP117 (ID=0x%04X)" % chip_id)
else:
    print("Unknown device: ID=0x%04X, expected 0x%04X" % (chip_id, TMP117_CHIP_ID))
    raise RuntimeError("Device ID verification failed - not a TMP117")

# 创建 TMP117 驱动实例
tmp = TMP117(i2c, address=TMP117_I2C_ADDR, debug=False)
print("TMP117 driver initialized successfully")
print("Initial temperature: %.4f C" % tmp.temperature)
print("Measurement mode: %s" % tmp.measurement_mode)
print("Averaging: %s" % tmp.averaging_measurements)
print("=" * 50)
print("Main loop started — printing temperature every %d ms" % PRINT_INTERVAL_MS)
last_print_time = time.ticks_ms()

# ====================  主程序  ====================

try:
    while True:
        current_time = time.ticks_ms()
        # 按间隔打印温度（低频核心 API，自动执行）
        elapsed_ms = time.ticks_diff(current_time, last_print_time)
        if elapsed_ms >= PRINT_INTERVAL_MS:
            temp = tmp.temperature
            print("Temperature: %.4f C" % temp)
            last_print_time = current_time

        # Optional manual test snippets:
        # - Alert config: set tmp.high_limit / tmp.low_limit and read status.
        # - Mode switch: set tmp.measurement_mode and read tmp.temperature.
        # - Averaging: set tmp.averaging_measurements before reading.
        # - Boundary values: set limits to 255.0 and -256.0.
        # - Invalid params: assign invalid values inside try/except.

        time.sleep_ms(100)

except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    # 清理资源：关断传感器 + 释放 I2C 引用
    print("Cleaning up resources...")
    tmp.deinit()
    del tmp
    print("Program exited")
