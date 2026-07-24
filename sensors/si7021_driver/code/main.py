# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Chris Balmer
# @File    : main.py
# @Description : 测试 Si7021 温湿度传感器驱动类
# @License : MIT

import time
from machine import Pin, I2C
import si7021

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================
# I2C 总线引脚配置（根据实际接线修改）
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000

# Si7021 默认 I2C 地址
SI7021_ADDR = 0x40

# 设备识别常量
_EXPECTED_ID_PREFIX = "Si70"  # 期望的设备型号前缀（Si7020/Si7021）

# 定时打印控制
last_print_time = 0
print_interval = 2000  # 打印间隔（ms）

# ======================================== 功能函数 ============================================


def print_device_info(sensor):
    """
    打印设备基本信息（低频，自动执行）
    ==========================================
    Print device basic info (low frequency, auto-execute).
    """
    print("Serial:     %d" % sensor.serial)
    print("Identifier: %s" % sensor.identifier)


def print_temperature_fahrenheit(sensor):
    """
    打印华氏温度（扩展功能，默认注释调用，可 REPL 手动调用）
    ==========================================
    Print Fahrenheit temperature (extended, commented by default, REPL manual call).
    """
    f = (getattr(si7021, "convert_celcius_to_fahrenheit")(sensor.temperature),)[0]
    print("Fahrenheit: %.2f F" % f)


def do_reset(sensor):
    """
    软复位传感器（模式切换，默认注释调用，可 REPL 手动触发）
    ==========================================
    Soft-reset sensor (mode switch, commented by default, REPL manual trigger).
    """
    getattr(sensor, "reset")()
    print("Sensor reset complete")


def test_debug_mode(i2c):
    """
    边界参数测试：启用调试日志模式创建传感器实例
    打印初始化日志后立即释放，避免占用 I2C 总线
    ==========================================
    Boundary test: create sensor with debug mode enabled.
    Prints init log then releases immediately to free I2C bus.
    """
    print("--- Boundary: debug=True mode ---")
    si7021_cls = si7021.Si7021
    sensor_dbg = (si7021_cls(i2c, address=SI7021_ADDR, debug=True),)[0]
    print("  Temperature (debug mode): %.2f C" % sensor_dbg.temperature)
    print("  Humidity (debug mode):    %.2f %%RH" % sensor_dbg.relative_humidity)
    getattr(sensor_dbg, "deinit")()
    print("--- Debug mode test done ---")


def test_invalid_params(i2c):
    """
    异常参数测试：验证非法参数是否正确抛出异常
    ==========================================
    Exception test: verify invalid parameters raise proper exceptions.
    """
    print("--- Exception test: invalid address ---")
    try:
        si7021_cls = si7021.Si7021
        _ = (si7021_cls(i2c, address=0x80),)[0]
        print("  FAIL: expected ValueError was not raised")
    except ValueError as e:
        print("  OK: ValueError raised: %s" % e)

    print("--- Exception test: invalid debug type ---")
    try:
        si7021_cls = si7021.Si7021
        _ = (si7021_cls(i2c, address=SI7021_ADDR, debug="yes"),)[0]
        print("  FAIL: expected ValueError was not raised")
    except ValueError as e:
        print("  OK: ValueError raised: %s" % e)

    print("--- Exception test: read-only property ---")
    si7021_cls = si7021.Si7021
    sensor_tmp = (si7021_cls(i2c, address=SI7021_ADDR),)[0]
    try:
        sensor_tmp.temperature = 25.0
        print("  FAIL: expected AttributeError was not raised")
    except AttributeError as e:
        print("  OK: AttributeError raised: %s" % e)
    getattr(sensor_tmp, "deinit")()
    print("--- Exception test done ---")


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
# 上电稳定延时，确保传感器就绪
time.sleep(3)
print("FreakStudio: Si7021 Temperature & Humidity Sensor Test")

# 硬件初始化：创建 I2C 总线实例
i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# I2C 总线设备扫描
devices = i2c.scan()
print("I2C scan result: %s" % str([hex(addr) for addr in devices]))
if not devices:
    raise RuntimeError("No I2C device found on bus")
# 验证目标地址是否存在
if SI7021_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X, found: %s" % (SI7021_ADDR, str([hex(a) for a in devices])))

# 创建传感器实例（正常参数场景：默认地址、无调试日志）
sensor = si7021.Si7021(i2c, address=SI7021_ADDR, debug=False)
last_print_time = time.ticks_ms()

# 设备 ID 验证：确认传感器型号为 Si702x 系列
if sensor.identifier.startswith(_EXPECTED_ID_PREFIX):
    print("Device found: %s (serial: %d)" % (sensor.identifier, sensor.serial))
else:
    print("Warning: Unexpected device identifier: %s" % sensor.identifier)

# ========================================  主程序  ===========================================
try:
    # 首次打印完整设备信息
    print_device_info(sensor)

    # 执行边界参数和异常参数测试（一次性，注释自动执行，可 REPL 手动调用）
    # test_debug_mode(i2c)
    # test_invalid_params(i2c)

    while True:
        current_time = time.ticks_ms()
        # 定时打印温湿度数据
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 核心数据采集：读取温度（℃）和相对湿度（%RH）
            temp = sensor.temperature
            rh = sensor.relative_humidity
            print("Temperature: %.2f C  |  Humidity: %.2f %%RH" % (temp, rh))
            last_print_time = current_time

        # print_temperature_fahrenheit(sensor)  # 扩展：华氏温度转换，可 REPL 手动调用
        # do_reset(sensor)                       # 模式切换：软复位，可 REPL 手动触发

        # 短暂休眠，避免占用 CPU
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except si7021.CRCError as e:
    print("CRC check error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
