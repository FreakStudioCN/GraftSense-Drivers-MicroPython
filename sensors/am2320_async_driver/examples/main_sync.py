# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Mike Causer
# @File    : main.py
# @Description : 测试AM2320温湿度传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================
from machine import I2C, Pin
import time
import micropython
from am2320 import AM2320

# （模块导入已在文件头部完成）

# ======================================== 全局变量 ============================================


# 打印间隔（毫秒）
_PRINT_INTERVAL_MS = 2000

# I2C 引脚配置（请根据实际接线修改）
_I2C_SCL_PIN = 5
_I2C_SDA_PIN = 4
_I2C_FREQ = 100000

# AM2320 固定 I2C 地址
_AM2320_I2C_ADDR = 0x5C

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
micropython.alloc_emergency_exception_buf(100)

# 上电等待传感器稳定
time.sleep(3)
print("FreakStudio: AM2320 temperature and humidity sensor test")

# 初始化 I2C 总线（引脚号请根据实际接线修改）
i2c = I2C(0, scl=Pin(_I2C_SCL_PIN), sda=Pin(_I2C_SDA_PIN), freq=_I2C_FREQ)
print("I2C bus initialized: SCL=Pin(%d), SDA=Pin(%d)" % (_I2C_SCL_PIN, _I2C_SDA_PIN))

# 扫描 I2C 总线，检测设备是否存在
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 检查 AM2320 目标地址是否在扫描列表中
if _AM2320_I2C_ADDR not in devices:
    raise RuntimeError("AM2320 not found at expected address 0x%02X" % _AM2320_I2C_ADDR)
print("AM2320 found at 0x%02X" % _AM2320_I2C_ADDR)

# 注意：AM2320 无芯片 ID 寄存器，已通过 I2C 地址扫描确认设备存在
# 注：如需验证设备通信，可手动调用 sensor.check()

# 实例化传感器驱动
sensor = AM2320(i2c)
print("Sensor driver initialized")

# 执行初始测量
sensor.measure()
print("Initial reading - Temperature: %.1f C, Humidity: %.1f %%" % (sensor.temperature(), sensor.humidity()))

last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        # 按间隔定时打印温湿度数据
        if time.ticks_diff(current_time, last_print_time) >= _PRINT_INTERVAL_MS:
            # 触发一次测量（唤醒传感器→发送读命令→读取数据→CRC校验）
            sensor.measure()
            # 分别获取温度和湿度值
            temp = sensor.temperature()
            hum = sensor.humidity()
            print("Temperature: %.1f C, Humidity: %.1f %%" % (temp, hum))
            last_print_time = current_time
        # 主循环短延时，避免 CPU 空转
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    # 释放传感器驱动资源
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
