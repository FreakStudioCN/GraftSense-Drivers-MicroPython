# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 00:00
# @Author  : Mike Causer
# @File    : main.py
# @Description : 测试 LM75A 数字温度传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time
from lm75a import LM75A

# ======================================== 全局变量 ============================================

# I2C 引脚和频率配置（ESP32 默认 I2C0: SCL=GPIO22, SDA=GPIO21）
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000

# LM75A 默认 I2C 地址（A2=A1=A0=0）
LM75A_ADDR = 0x48

# 温度打印间隔（ms）
PRINT_INTERVAL_MS = 2000
# 上次打印时间戳（ms）
last_print_time = 0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Testing LM75A digital temperature sensor driver")

# 硬件初始化：ESP32 I2C0 默认引脚
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# I2C 总线设备扫描
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")

print("I2C devices found: %s" % [hex(d) for d in devices])

# 查找 LM75A 目标地址
if LM75A_ADDR not in devices:
    raise RuntimeError("LM75A not found at address 0x%02X" % LM75A_ADDR)

# LM75A 无芯片 ID 寄存器（仅含 Temp/Conf/Thyst/Tos），设备验证由构造器 check() 完成
print("LM75A found at address 0x%02X" % LM75A_ADDR)

# 实例化传感器，启用调试日志观察寄存器读写
sensor = LM75A(i2c, address=LM75A_ADDR, debug=True)

# 初始化默认温度阈值
sensor.thyst(24.0)
sensor.tos(27.0)

print("LM75A initialization complete")
print("Temperature precision: 0.125C | Threshold precision: 0.5C")
print("----------------------------------------")

# ========================================  主程序  ===========================================

try:
    last_print_time = time.ticks_ms()
    while True:
        current_time = time.ticks_ms()
        # 低频查询：读取温度并打印
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            t = sensor.temp()
            print("Temperature: %.2f C" % t)
            last_print_time = current_time

        # Optional manual test snippets:
        # - Comparator mode: sensor.config(os_mode=0); print("OS mode: comparator")
        # - Interrupt mode: sensor.config(os_mode=1); print("OS mode: interrupt")
        # - Shutdown mode: sensor.config(shutdown=1); print("Device entered shutdown mode")
        # - Normal mode: sensor.config(shutdown=0); print("Device resumed normal mode")
        # - Thresholds: sensor.thyst(24.0); sensor.tos(27.0)
        # - Boundary thresholds: sensor.thyst(-55.0); sensor.tos(125.0)
        # - Invalid params: call sensor.tos(200.0) or sensor.thyst(-100.0) in try/except

        time.sleep_ms(100)

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
