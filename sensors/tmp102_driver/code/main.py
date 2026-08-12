# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Kevin Houlihan
# @File    : main.py
# @Description : 测试 TMP102 数字温度传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin

# 导入驱动核心与全部扩展模块
from _tmp102 import Tmp102
import alert
import conversionrate
import extendedmode
import shutdown
import oneshot
from convertors import Fahrenheit, Kelvin

# 这些模块在导入时向 Tmp102 注入相应的可选 API；保留引用确保扩展已加载。
_EXTENSION_MODULES = (alert, conversionrate, extendedmode, shutdown, oneshot)


# ======================================== 全局变量 ============================================

# TMP102 默认 I2C 地址（ADDR0 引脚接 GND）
_TMP102_ADDR = 0x48

# 打印间隔（毫秒）
_PRINT_INTERVAL_MS = 2000

# 上次打印时间戳
_last_print_time = 0

_sleep = time.sleep
_sleep_ms = time.sleep_ms

# ======================================== 功能函数 ============================================


def demo_conversion_rates(sensor: object) -> None:
    """
    演示四档转换速率切换（模式切换，可 REPL 手动调用）
    ==========================================
    Demonstrate all four conversion rate settings (mode switch, call from REPL)
    """
    print("--- Conversion Rate Demo ---")
    # 0.25 Hz
    sensor.conversion_rate = Tmp102.CONVERSION_RATE_QUARTER_HZ
    print("Rate: 0.25 Hz (CR=00)")
    _sleep(0.5)
    # 1 Hz
    sensor.conversion_rate = Tmp102.CONVERSION_RATE_1HZ
    print("Rate: 1 Hz (CR=01)")
    _sleep(0.5)
    # 4 Hz (default)
    sensor.conversion_rate = Tmp102.CONVERSION_RATE_4HZ
    print("Rate: 4 Hz (CR=10, default)")
    _sleep(0.5)
    # 8 Hz
    sensor.conversion_rate = Tmp102.CONVERSION_RATE_8HZ
    print("Rate: 8 Hz (CR=11)")


def demo_extended_mode(sensor: object) -> None:
    """
    演示扩展模式切换（模式切换，可 REPL 手动调用）
    ==========================================
    Demonstrate extended mode toggle (mode switch, call from REPL)
    """
    print("--- Extended Mode Demo ---")
    # 启用 13-bit 扩展模式
    sensor.extended_mode = True
    print("Extended mode: ON (13-bit, max 150C)")
    _sleep(0.3)
    # 读取扩展模式下的温度
    print("Temperature (extended): %.4f C" % sensor.temperature)
    # 恢复 12-bit 正常模式
    sensor.extended_mode = False
    print("Extended mode: OFF (12-bit, max 128C)")


def demo_alert_config(sensor: object) -> None:
    """
    演示告警/温控器配置（模式切换，可 REPL 手动调用）
    ==========================================
    Demonstrate alert/thermostat configuration (mode switch, call from REPL)
    """
    print("--- Alert/Thermostat Config Demo ---")
    # 告警极性
    sensor.alert_polarity = Tmp102.ALERT_HIGH
    print("Alert polarity: ALERT_HIGH")
    sensor.alert_polarity = Tmp102.ALERT_LOW
    print("Alert polarity: ALERT_LOW (default)")
    # 温控器模式
    sensor.thermostat_mode = Tmp102.INTERRUPT_MODE
    print("Thermostat mode: INTERRUPT")
    sensor.thermostat_mode = Tmp102.COMPARATOR_MODE
    print("Thermostat mode: COMPARATOR (default)")
    # 故障队列长度
    sensor.fault_queue_length = Tmp102.FAULT_QUEUE_4
    print("Fault queue: 4 faults")
    sensor.fault_queue_length = Tmp102.FAULT_QUEUE_1
    print("Fault queue: 1 fault (default)")
    # 读取告警标志
    print("Alert flag: %s" % ("HIGH" if sensor.alert else "LOW"))


def demo_threshold_config(sensor: object) -> None:
    """
    演示温度阈值配置（模式切换，可 REPL 手动调用）
    ==========================================
    Demonstrate temperature threshold config (mode switch, call from REPL)
    """
    print("--- Threshold Config Demo ---")
    # 设置高温阈值
    sensor.thermostat_high_temperature = 35.0
    print("High threshold: 35.0 C")
    # 设置低温阈值
    sensor.thermostat_low_temperature = 10.0
    print("Low threshold: 10.0 C")
    # 验证读取
    print("Read back high: %.2f C" % sensor.thermostat_high_temperature)
    print("Read back low: %.2f C" % sensor.thermostat_low_temperature)


def demo_shutdown_oneshot(sensor: object) -> None:
    """
    演示关断模式与单次转换（模式切换，可 REPL 手动调用）
    ==========================================
    Demonstrate shutdown mode and one-shot conversion (mode switch, call from REPL)
    """
    print("--- Shutdown / One-Shot Demo ---")
    # 进入关断模式
    sensor.shutdown = True
    print("Shutdown: ON (low power)")
    _sleep(0.5)
    # 触发单次转换
    initiate_conversion = sensor.initiate_conversion
    initiate_conversion()
    print("One-shot conversion initiated...")
    # 等待转换完成
    for _ in range(100):
        if sensor.conversion_ready:
            break
        _sleep_ms(10)
    else:
        raise RuntimeError("Timed out waiting for one-shot conversion")
    print("Conversion ready!")
    # 读取单次转换结果
    print("One-shot temperature: %.4f C" % sensor.temperature)
    # 唤醒设备
    sensor.shutdown = False
    print("Shutdown: OFF (awake)")


def demo_temperature_convertors(sensor: object) -> None:
    """
    演示温度单位转换器（工具类，可 REPL 手动调用）
    ==========================================
    Demonstrate temperature unit converters (utility, call from REPL)
    """
    print("--- Temperature Converter Demo ---")
    temp_c = sensor.temperature
    # 华氏度
    convert_to_fahrenheit = (Fahrenheit()).convert_to
    print("Celsius: %.2f C  →  Fahrenheit: %.2f F" % (temp_c, convert_to_fahrenheit(temp_c)))
    # 开尔文
    convert_to_kelvin = (Kelvin()).convert_to
    print("Celsius: %.2f C  →  Kelvin: %.2f K" % (temp_c, convert_to_kelvin(temp_c)))


def demo_exception_handling() -> None:
    """
    演示异常参数处理（异常验证，可 REPL 手动调用）
    ==========================================
    Demonstrate exception handling (exception verification, call from REPL)
    """
    print("--- Exception Handling Demo ---")
    # 非法 I2C 地址
    try:
        Tmp102(i2c, 0x80)
    except ValueError as e:
        print("ValueError (bad address): %s" % e)
    # 非法 kwargs（未导入对应扩展模块时传入未知配置键）
    try:
        Tmp102(i2c, _TMP102_ADDR, unknown_key=True)
    except ValueError as e:
        print("ValueError (unknown key): %s" % e)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: TMP102 I2C Temperature Sensor Test")
print("Platform: MicroPython v1.23")

# ---- I2C 初始化 ----
# RP2040: I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
print("I2C bus initialized (freq=400kHz)")

# ---- I2C 设备扫描 ----
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))
# 验证 TMP102 是否在期望地址上
if _TMP102_ADDR not in devices:
    raise RuntimeError("TMP102 not found at expected address 0x%02X" % _TMP102_ADDR)
print("TMP102 found at 0x%02X" % _TMP102_ADDR)

# ---- TMP102 实例化 ----
sensor = Tmp102(i2c, _TMP102_ADDR)
print("TMP102 initialized (default: 4Hz, 12-bit, Celsius)")
print("Device config register OK (basic verification passed)")

initial_temp = sensor.temperature
print("Initial temperature: %.4f C" % initial_temp)
_last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()

        # 定时打印温度值（低频核心 API，自动执行）
        if time.ticks_diff(current_time, _last_print_time) >= _PRINT_INTERVAL_MS:
            temp = sensor.temperature
            print("[%d ms] Temperature: %.4f C" % (current_time, temp))
            _last_print_time = current_time

        # ---- 以下功能默认注释，可在 REPL 中手动调用 ----
        # demo_conversion_rates(sensor)       # 转换速率切换演示
        # demo_extended_mode(sensor)          # 扩展模式切换演示
        # demo_alert_config(sensor)           # 告警/温控器配置演示
        # demo_threshold_config(sensor)       # 温度阈值配置演示
        # demo_shutdown_oneshot(sensor)       # 关断模式与单次转换演示
        # demo_temperature_convertors(sensor) # 温度单位转换演示
        # demo_exception_handling()     # 异常参数验证演示

        # 短延时避免 CPU 满载
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
