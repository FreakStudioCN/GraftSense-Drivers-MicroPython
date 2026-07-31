# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : mimingxuan
# @File    : main.py
# @Description : 测试 SHT35 驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import Pin, I2C
from time import sleep_ms
import time
from sht35 import (
    SHT35,
    SHT35_DEFAULT_ADDR,
    REPEATABILITY_HIGH,
    REPEATABILITY_MEDIUM,
    REPEATABILITY_LOW,
)

# ======================================== 全局变量 ============================================

# I2C 引脚配置（请根据实际接线修改）
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
I2C_ID = 0

# 设备 I2C 目标地址
DEVICE_ADDR = SHT35_DEFAULT_ADDR  # 0x44

# 打印间隔（ms）
PRINT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================


def print_raw_data(sensor):
    """
    打印原始计数值
    高频数据读取，默认注释调用，可在 REPL 中手动调用：
        >>> print_raw_data(sensor)
    """
    raw_values = (getattr(sensor, "read_raw")(),)[0]
    temp_ticks, humi_ticks = raw_values
    print("Raw ticks - Temperature: %d, Humidity: %d" % (temp_ticks, humi_ticks))


def test_boundary_params(sensor):
    """
    测试边界参数：不同重复性等级
    验证三种重复性模式下的数据输出差异，可在 REPL 中手动调用：
        >>> test_boundary_params(sensor)
    """
    print("=== Boundary Test: Repeatability Levels ===")
    level_names = {
        REPEATABILITY_HIGH: "HIGH",
        REPEATABILITY_MEDIUM: "MEDIUM",
        REPEATABILITY_LOW: "LOW",
    }
    for level in (REPEATABILITY_HIGH, REPEATABILITY_MEDIUM, REPEATABILITY_LOW):
        measurement = (getattr(sensor, "measure")(repeatability=level),)[0]
        temp, humi = measurement
        print("  %s: T=%.2f C, H=%.2f %%RH" % (level_names[level], temp, humi))
        sleep_ms(100)


def test_fahrenheit(sensor):
    """
    测试华氏度输出
    验证 celsius=False 时的温度转换，可在 REPL 中手动调用：
        >>> test_fahrenheit(sensor)
    """
    measurement = (getattr(sensor, "measure")(celsius=False),)[0]
    temp_f, humi = measurement
    print("Fahrenheit: T=%.2f F, H=%.2f %%RH" % (temp_f, humi))


def test_exception_params(sensor):
    """
    测试异常参数处理
    验证非法参数是否正确抛出 ValueError，可在 REPL 中手动调用：
        >>> test_exception_params(sensor)
    """
    print("=== Exception Test: Invalid Repeatability ===")
    try:
        getattr(sensor, "measure")(repeatability=99)
        print("  FAIL: Expected ValueError was not raised")
    except ValueError as e:
        print("  PASS: Caught expected ValueError: %s" % str(e))

    print("=== Exception Test: Invalid Clock Stretch ===")
    try:
        getattr(sensor, "read_raw")(repeatability=99)
        print("  FAIL: Expected ValueError was not raised")
    except ValueError as e:
        print("  PASS: Caught expected ValueError: %s" % str(e))


def test_status_functions(sensor):
    """
    测试状态管理和加热器功能
    模式切换类操作，可在 REPL 中手动调用：
        >>> test_status_functions(sensor)
    """
    print("=== Status & Heater Test ===")
    # 读取状态寄存器
    status = (getattr(sensor, "read_status")(),)[0]
    print("  Status register: 0x%04X" % status)
    # 清除状态寄存器
    getattr(sensor, "clear_status")()
    print("  Status cleared")
    # 开启加热器
    getattr(sensor, "heater")(True)
    print("  Heater ON (wait 500ms)")
    sleep_ms(500)
    # 测量加热后的温湿度
    measurement = (getattr(sensor, "measure")(),)[0]
    temp, humi = measurement
    print("  Heater ON  -> T=%.2f C, H=%.2f %%RH" % (temp, humi))
    # 关闭加热器
    getattr(sensor, "heater")(False)
    print("  Heater OFF")
    # 软复位传感器
    getattr(sensor, "reset")()
    print("  Sensor reset complete")


def test_clock_stretch(sensor):
    """
    测试时钟拉伸模式
    验证 clock_stretch=True 下的测量，可在 REPL 中手动调用：
        >>> test_clock_stretch(sensor)
    """
    print("=== Clock Stretch Test ===")
    measurement = (getattr(sensor, "measure")(clock_stretch=True),)[0]
    temp, humi = measurement
    print("  Clock stretch: T=%.2f C, H=%.2f %%RH" % (temp, humi))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

print("FreakStudio: Testing SHT35 temperature and humidity sensor driver")

# 等待硬件就绪
time.sleep(3)

# 初始化 I2C 总线
i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
print("I2C initialized: scl=Pin(%d), sda=Pin(%d), freq=%dHz" % (I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ))

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found %d device(s): %s" % (len(devices), str([hex(d) for d in devices])))

# 验证目标设备是否在线
if DEVICE_ADDR not in devices:
    raise RuntimeError("SHT35 not found at address 0x%02X" % DEVICE_ADDR)

# 实例化传感器（依赖注入）
sensor = SHT35(i2c, addr=DEVICE_ADDR, debug=False)
last_print_time = time.ticks_ms()

# 通过读取状态寄存器验证设备身份（SHT35 无标准 Chip ID 寄存器）
print("Verifying device identity...")
try:
    status = (getattr(sensor, "read_status")(),)[0]
    print("Device verified at 0x%02X, status=0x%04X" % (DEVICE_ADDR, status))
except RuntimeError as e:
    print("WARNING: Status read failed: %s" % str(e))
    print("Device may still work - proceeding with test")

# 初始化打印计时器
last_print_time = 0

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        # 定时打印温湿度数据（低频核心 API，自动执行）
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            temperature, humidity = sensor.measure()
            print("Temperature: %.2f C, Humidity: %.2f %%RH" % (temperature, humidity))
            last_print_time = current_time

        # 以下为高频/模式切换/边界测试函数，默认注释，可通过 REPL 手动调用：
        # print_raw_data(sensor)              # 高频：打印原始计数值
        # test_boundary_params(sensor)        # 边界：测试所有重复性等级
        # test_fahrenheit(sensor)             # 边界：华氏度输出
        # test_exception_params(sensor)       # 异常：非法参数测试
        # test_status_functions(sensor)       # 模式切换：状态/加热器/复位测试
        # test_clock_stretch(sensor)          # 边界：时钟拉伸模式

        sleep_ms(100)

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
