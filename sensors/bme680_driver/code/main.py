# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Limor 'Ladyada' Fried, Jeff Raber
# @File    : main.py
# @Description : BME680 传感器驱动测试代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from bme680 import BME680_I2C

# ======================================== 全局变量 ============================================

# --- I2C 引脚配置（Raspberry Pi Pico / RP2040） ---
# 也可使用 SPI 模式：from bme680 import BME680_SPI
I2C_ID = 0
SDA_PIN = 0
SCL_PIN = 1
I2C_FREQ = 400000

# --- BME680 设备地址 ---
# SDO 接 GND → 0x77（默认），SDO 接 VDD → 0x76
BME680_I2C_ADDR = 0x77
BME680_ALT_ADDR = 0x76

# --- 芯片 ID 验证参数 ---
BME680_CHIP_ID_REG = 0xD0
BME680_CHIP_ID_VAL = 0x61

# --- 打印控制 ---
PRINT_INTERVAL_MS = 2000
last_print_time = 0

# --- 传感器实例引用（初始化配置区创建） ---
bme = None

# ======================================== 功能函数 ============================================


def test_boundary_params():
    """
    测试边界参数：最大/最小过采样率和滤波器
    注释自动调用，可 REPL 手动执行
    """
    global bme
    print("--- Boundary Parameter Test ---")

    # 测试最大过采样率
    bme.temperature_oversample = 16
    bme.pressure_oversample = 16
    bme.humidity_oversample = 16
    print("Max oversample (16x): temp=%.2f C, pres=%.2f hPa, hum=%.2f %%" % (bme.temperature, bme.pressure, bme.humidity))

    # 测试最小过采样率（跳过采样，仅返回上次值或默认值）
    bme.temperature_oversample = 0
    bme.pressure_oversample = 0
    bme.humidity_oversample = 0
    print("Min oversample (skip): temp=%.2f C, pres=%.2f hPa, hum=%.2f %%" % (bme.temperature, bme.pressure, bme.humidity))

    # 测试最大滤波器
    bme.filter_size = 127
    print("Max filter (127): temp=%.2f C" % bme.temperature)
    # 测试最小滤波器
    bme.filter_size = 0
    print("Min filter (0): temp=%.2f C" % bme.temperature)

    # 恢复默认配置
    bme.temperature_oversample = 4
    bme.pressure_oversample = 3
    bme.humidity_oversample = 2
    bme.filter_size = 3
    print("--- Boundary test done, defaults restored ---")


def test_exception_params():
    """
    测试异常参数：非法过采样率/滤波器值应正确抛出 ValueError
    注释自动调用，可 REPL 手动执行
    """
    global bme
    print("--- Exception Parameter Test ---")

    # 测试非法过采样率
    try:
        bme.temperature_oversample = 99
    except ValueError as e:
        print("Caught expected: %s" % e)

    # 测试非法滤波器值
    try:
        bme.filter_size = 255
    except ValueError as e:
        print("Caught expected: %s" % e)

    print("--- Exception test done ---")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: BME680 Temperature/Humidity/Pressure/Gas Sensor Test")
print("=" * 60)

# 初始化 I2C 总线
i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)

# I2C 设备扫描
devices = i2c.scan()
print("I2C bus scan result: %s" % (["0x%02x" % d for d in devices] if devices else "No devices found"))

if not devices:
    raise RuntimeError("No I2C device found on bus %d" % I2C_ID)

# 自动检测 BME680 地址
sensor_addr = BME680_I2C_ADDR if BME680_I2C_ADDR in devices else (BME680_ALT_ADDR if BME680_ALT_ADDR in devices else None)

if sensor_addr is None:
    raise RuntimeError("BME680 not found at 0x%02x or 0x%02x. Check wiring and SDO pin." % (BME680_I2C_ADDR, BME680_ALT_ADDR))

print("BME680 candidate at 0x%02x, verifying chip ID..." % sensor_addr)

# 芯片 ID 验证（通过直接读取寄存器进行预检）
# 此步骤在实例化驱动之前，用原始 I2C 读取确认硬件存在
try:
    chip_id = i2c.readfrom_mem(sensor_addr, BME680_CHIP_ID_REG, 1)[0]
    if chip_id == BME680_CHIP_ID_VAL:
        print("Device found: BME680 (chip ID 0x%02x verified)" % chip_id)
    else:
        print("Device not found: unexpected chip ID 0x%02x (expected 0x%02x)" % (chip_id, BME680_CHIP_ID_VAL))
        raise RuntimeError("Chip ID mismatch")
except OSError as e:
    raise RuntimeError("I2C communication failed during chip ID check") from e

# 实例化传感器（默认配置）
bme = BME680_I2C(i2c, address=sensor_addr)
last_print_time = time.ticks_ms()

# 可选：修改采样配置（取消注释以启用）
# bme.temperature_oversample = 8   # 温度 8 倍过采样
# bme.pressure_oversample = 4      # 压力 4 倍过采样
# bme.humidity_oversample = 4      # 湿度 4 倍过采样
# bme.filter_size = 7              # IIR 滤波器大小 7
# bme.sea_level_pressure = 1013.25 # 海平面气压校准

print("BME680 initialized successfully at 0x%02x" % sensor_addr)
print("Oversampling: T=%dx P=%dx H=%dx  Filter=%d" % (bme.temperature_oversample, bme.pressure_oversample, bme.humidity_oversample, bme.filter_size))
print("=" * 60)

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        # 按打印间隔输出低频核心数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            print(
                "T: %.2f C  H: %.2f %%  P: %.2f hPa  Gas: %d ohm  Alt: %.2f m" % (bme.temperature, bme.humidity, bme.pressure, bme.gas, bme.altitude)
            )
            last_print_time = current_time

        # test_boundary_params()   # 边界测试：最大/最小过采样率与滤波器
        # test_exception_params()  # 异常测试：非法参数校验
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if bme is not None:
        bme.deinit()
        del bme
    print("Program exited")
