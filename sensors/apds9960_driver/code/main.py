# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Rune Langøy
# @File    : main.py
# @Description : 测试 APDS9960LITE 驱动类 —— 环境光、颜色（RGBC）、接近检测
# @License : MIT

# ======================================== 导入相关模块 =========================================

import machine
import time
from apds9960LITE import APDS9960LITE

# ======================================== 全局变量 ============================================

# APDS9960 I2C 地址和芯片 ID 常量
APDS9960_ADDR = 0x39
APDS9960_ID_REG = 0x92
# APDS9960 可能的芯片 ID 值
APDS9960_IDS = (0xAB, 0xA8, 0x9C, 0x9E)

# 引脚定义（GPIO 编号，对应 Raspberry Pi Pico / ESP32 等平台）
SDA_PIN = 4
SCL_PIN = 5

# 传感器数据打印间隔（毫秒）
PRINT_INTERVAL_MS = 2000
last_print_time = 0

# ALS 增益值常量引用（来自 ALS 类）
GAIN_1X = 0
GAIN_2X = 1
GAIN_16X = 2
GAIN_64X = 3

# 接近增益常量引用（来自 PROX 类）
PGAIN_1X = 0
PGAIN_2X = 1
PGAIN_4X = 2
PGAIN_8X = 3

# LED 电流常量引用（来自 PROX 类）
LED_100MA = 0
LED_50MA = 1
LED_25MA = 2
LED_12_5MA = 3

# I2C 总线实例（在初始化配置区实例化）
i2c = None
apds9960 = None

# ======================================== 功能函数 ============================================


def test_boundary_params():
    """
    边界参数场景：测试增益和中断阈值的极限值
    此函数演示硬件极限参数的设置，可 REPL 手动调用
    """
    print("--- Testing boundary parameters ---")

    # 测试 ALS 增益边界值：最小值 0（1x）和最大值 3（64x）
    print("Testing ALS gain min (0=1x)...")
    apds9960.als.eLightGain = GAIN_1X
    print("  ALS gain set to 1x")
    getattr(time, "sleep_ms")(500)

    print("Testing ALS gain max (3=64x)...")
    apds9960.als.eLightGain = GAIN_64X
    print("  ALS gain set to 64x")
    getattr(time, "sleep_ms")(500)

    # 恢复默认增益
    apds9960.als.eLightGain = GAIN_1X
    print("  ALS gain restored to 1x")

    # 测试接近增益边界值
    print("Testing proximity gain min (0=1x)...")
    apds9960.prox.eProximityGain = PGAIN_1X
    print("  Proximity gain set to 1x")
    getattr(time, "sleep_ms")(500)

    print("Testing proximity gain max (3=8x)...")
    apds9960.prox.eProximityGain = PGAIN_8X
    print("  Proximity gain set to 8x")
    getattr(time, "sleep_ms")(500)

    # 恢复默认增益
    apds9960.prox.eProximityGain = PGAIN_1X
    print("  Proximity gain restored to 1x")

    # 测试 LED 电流边界值
    print("Testing LED current min (3=12.5mA)...")
    apds9960.prox.eLEDCurrent = LED_12_5MA
    print("  LED current set to 12.5mA")
    getattr(time, "sleep_ms")(500)

    print("Testing LED current max (0=100mA)...")
    apds9960.prox.eLEDCurrent = LED_100MA
    print("  LED current set to 100mA")
    getattr(time, "sleep_ms")(500)

    # 恢复默认电流
    apds9960.prox.eLEDCurrent = LED_100MA
    print("  LED current restored to 100mA")

    # 测试中断阈值边界值
    print("Testing ALS interrupt threshold boundary...")
    getattr(apds9960.als, "setInterruptThreshold")(high=0, low=1025, persistance=0)
    print("  ALS threshold set to high=0, low=1025, persistance=0")

    print("Testing proximity interrupt threshold boundary...")
    getattr(apds9960.prox, "setInterruptThreshold")(high=0, low=255, persistance=0)
    print("  Proximity threshold set to high=0, low=255, persistance=0")

    print("--- Boundary parameter test complete ---")


def test_exception_params():
    """
    异常参数场景：测试非法参数是否触发正确的异常
    此函数演示异常处理，可 REPL 手动调用
    """
    print("--- Testing exception parameters ---")

    # 测试 ALS 增益非法值
    print("Testing ALS gain invalid value (99)...")
    try:
        apds9960.als.eLightGain = 99
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 ALS 增益非法类型
    print("Testing ALS gain invalid type (string)...")
    try:
        apds9960.als.eLightGain = "invalid"
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试接近增益非法值
    print("Testing proximity gain invalid value (-1)...")
    try:
        apds9960.prox.eProximityGain = -1
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 LED 电流非法值
    print("Testing LED current invalid value (10)...")
    try:
        apds9960.prox.eLEDCurrent = 10
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 enableSensor 非法类型
    print("Testing enableSensor invalid type...")
    try:
        getattr(apds9960.als, "enableSensor")("yes")
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 powerOn 非法类型
    print("Testing powerOn invalid type...")
    try:
        getattr(apds9960, "powerOn")(1)
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    print("--- Exception parameter test complete ---")


def switch_to_high_gain_mode():
    """
    切换到高增益模式（模式切换，默认注释调用，可 REPL 手动触发）
    适用于暗光环境下的检测
    """
    apds9960.als.eLightGain = GAIN_64X
    apds9960.prox.eProximityGain = PGAIN_8X
    print("Switched to high-gain mode (ALS: 64x, Proximity: 8x)")


def switch_to_low_gain_mode():
    """
    切换到低增益模式（模式切换，默认注释调用，可 REPL 手动触发）
    适用于强光环境下的检测
    """
    apds9960.als.eLightGain = GAIN_1X
    apds9960.prox.eProximityGain = PGAIN_1X
    print("Switched to low-gain mode (ALS: 1x, Proximity: 1x)")


def enable_interrupts():
    """
    启用硬件中断功能（模式切换，默认注释调用，可 REPL 手动触发）
    """
    getattr(apds9960.als, "setInterruptThreshold")(high=500, low=20, persistance=4)
    getattr(apds9960.als, "enableInterrupt")(True)
    getattr(apds9960.prox, "setInterruptThreshold")(high=100, low=20, persistance=4)
    getattr(apds9960.prox, "enableInterrupt")(True)
    print("Hardware interrupts enabled for ALS and Proximity")


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)
print("FreakStudio: Testing APDS9960LITE driver module")

# 创建硬件 I2C 实例（I2C0: SCL=GP5, SDA=GP4）
print("Initializing I2C0 (SCL=GP%d, SDA=GP%d, 100kHz)..." % (SCL_PIN, SDA_PIN))
i2c = machine.I2C(0, scl=machine.Pin(SCL_PIN), sda=machine.Pin(SDA_PIN), freq=100000)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
print("I2C devices found: %s" % [hex(d) for d in devices])

# 检查总线上是否有设备
if len(devices) == 0:
    raise RuntimeError("No I2C device found on bus")

# 检查目标设备是否存在
if APDS9960_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % APDS9960_ADDR)

print("Device found at address 0x%02X" % APDS9960_ADDR)

# 读取芯片 ID 验证设备
print("Reading chip ID from register 0x%02X..." % APDS9960_ID_REG)
try:
    chip_id = i2c.readfrom_mem(APDS9960_ADDR, APDS9960_ID_REG, 1)[0]
    print("Chip ID: 0x%02X" % chip_id)
    if chip_id in APDS9960_IDS:
        print("Device confirmed: APDS9960 (ID 0x%02X matched)" % chip_id)
    else:
        print("Warning: Unexpected ID 0x%02X, expected one of %s" % (chip_id, [hex(v) for v in APDS9960_IDS]))
except OSError as e:
    raise RuntimeError("Failed to read chip ID register") from e

# 实例化 APDS9960LITE 驱动
print("Initializing APDS9960LITE driver (debug=False)...")
apds9960 = APDS9960LITE(i2c, debug=False)
last_print_time = time.ticks_ms()
print("APDS9960LITE driver initialized successfully")

# 正常参数场景：启用所有传感器
print("Enabling proximity sensor...")
apds9960.prox.enableSensor(True)

print("Enabling ALS sensor...")
apds9960.als.enableSensor(True)

# 正常参数场景：设置默认增益
apds9960.als.eLightGain = GAIN_1X
apds9960.prox.eProximityGain = PGAIN_1X
apds9960.prox.eLEDCurrent = LED_100MA
print("Default gain and current configured")

# 读取初始化后的状态寄存器
print("Initial status register: 0x%02X" % apds9960.statusRegister)

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()

        # 低频查询：按间隔打印所有传感器数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            last_print_time = current_time

            # 读取状态寄存器
            status = apds9960.statusRegister

            # 读取接近检测数据
            prox_val = apds9960.prox.proximityLevel

            # 读取环境光数据
            ambient = apds9960.als.ambientLightLevel
            red = apds9960.als.redLightLevel
            green = apds9960.als.greenLightLevel
            blue = apds9960.als.blueLightLevel

            # 输出传感器数据
            print("Status: 0x%02X | Prox: %3d | Ambient: %5d | " "R: %4d G: %4d B: %4d" % (status, prox_val, ambient, red, green, blue))

        # 以下为高频或模式切换 API，默认注释，可 REPL 手动调用：
        # test_boundary_params()        # 边界参数场景测试，REPL 中调用
        # test_exception_params()       # 异常参数场景测试，REPL 中调用
        # switch_to_high_gain_mode()    # 切换到高增益模式（暗光环境）
        # switch_to_low_gain_mode()     # 切换到低增益模式（强光环境）
        # enable_interrupts()           # 启用硬件中断功能

        # 短延时避免占用 CPU
        time.sleep_ms(50)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if apds9960 is not None:
        apds9960.deinit()
        del apds9960
    print("Program exited")
