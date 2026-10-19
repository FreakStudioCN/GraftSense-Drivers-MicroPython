# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31
# @Author  : Mike Causer
# @File    : main.py
# @Description : 测试 DHT12 温湿度传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from dht12 import DHT12

# ======================================== 全局变量 ============================================

# DHT12 固定 I2C 地址
DHT12_I2C_ADDR = 0x5C
# 打印间隔（ms）
PRINT_INTERVAL_MS = 2000
# 上次打印时间戳
_last_print_time = 0

# ======================================== 功能函数 ============================================


def scan_i2c_devices(i2c):
    """
    扫描 I2C 总线，返回设备地址列表
    """
    scan = i2c.scan
    return scan()


def find_dht12(i2c, expected_addr):
    """
    在 I2C 总线上查找 DHT12 传感器

    Args:
        i2c (I2C): I2C 总线实例
        expected_addr (int): 期望的传感器 I2C 地址

    Returns:
        bool: 找到传感器返回 True

    Raises:
        RuntimeError: 未在期望地址找到设备
    """
    device_found = False
    # 遍历扫描结果，打印设备地址并查找目标地址
    for addr in scan_i2c_devices(i2c):
        device_found = True
        print("I2C device found at 0x%02X" % addr)
        if addr == expected_addr:
            print("DHT12 found at 0x%02X" % addr)
            return True
    if device_found is False:
        raise RuntimeError("No I2C device found on the bus")
    raise RuntimeError("DHT12 not found at expected address 0x%02X" % expected_addr)


def test_invalid_params(i2c):
    """
    测试异常参数场景（边界/错误参数，注释默认执行，可 REPL 手动调用）

    覆盖场景：
    1. i2c=None → 预期 ValueError
    2. addr 超出 0x00~0x7F 范围 → 预期 ValueError
    3. addr 类型错误 → 预期 ValueError
    """
    print("=== Testing invalid parameters ===")

    # 场景 1：i2c=None
    try:
        DHT12(None)
    except ValueError as e:
        print("  [PASS] i2c=None raised ValueError: %s" % e)

    # 场景 2：addr 超出范围
    try:
        DHT12(i2c, addr=0x80)
    except ValueError as e:
        print("  [PASS] addr=0x80 raised ValueError: %s" % e)

    # 场景 3：addr 类型错误
    try:
        DHT12(i2c, addr="0x5C")
    except ValueError as e:
        print("  [PASS] addr='0x5C' raised ValueError: %s" % e)

    print("=== Parameter tests completed ===")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 等待 3 秒，确保硬件上电稳定
time.sleep(3)

print("FreakStudio: Testing DHT12 temperature and humidity sensor driver")

# 初始化 RP2040 的 I2C0 总线
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 扫描 I2C 总线并验证 DHT12 存在
find_dht12(i2c, DHT12_I2C_ADDR)

# 实例化传感器驱动
sensor = DHT12(i2c)
print("DHT12 driver initialized successfully")

# ========================================  主程序  ===========================================

try:
    # 边界参数场景：使用自定义地址实例化（与默认地址相同，验证参数传递正常）
    # sensor_custom = dht12.DHT12(i2c, addr=0x5C)  # 可 REPL 手动测试

    # 首次 sensor.check() 验证设备在线
    sensor.check()
    print("Sensor check passed")

    # 主循环：定期采集温湿度数据
    while True:
        current_time = time.ticks_ms()

        if time.ticks_diff(current_time, _last_print_time) >= PRINT_INTERVAL_MS:
            # 低频核心 API：保留自动执行
            sensor.measure()
            print("Temperature: %.1f C" % sensor.temperature())
            print("Humidity: %.1f %%" % sensor.humidity())
            _last_print_time = current_time

        # test_invalid_params(i2c)  # 异常参数测试，注释默认执行，可 REPL 手动调用
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % e)
except Exception as e:
    print("Unknown error: %s" % e)
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
