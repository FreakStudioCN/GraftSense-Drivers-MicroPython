# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2023/01/01 00:00
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 BMM150 三轴磁力计驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from micropython_bmm150 import bmm150

# ======================================== 全局变量 ============================================
# I2C 配置常量
I2C_BUS_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000

# BMM150 设备常量
BMM150_DEVICE_ID_REG = 0x40
BMM150_EXPECTED_ID = 0x32
BMM150_DEFAULT_ADDR = 0x13

# 打印间隔（毫秒）
print_interval = 500
last_print_time = 0

# ======================================== 功能函数 ============================================
def test_basic_measurements():
    """
    测试基本磁场测量功能
    """
    print("=== Testing Basic Measurements ===")
    magx, magy, magz, hall = bmm.measurements
    print("X-axis: %d uT" % magx)
    print("Y-axis: %d uT" % magy)
    print("Z-axis: %d uT" % magz)
    print("Hall resistance: %d" % hall)
    print()


def test_operation_modes():
    """
    测试操作模式切换
    """
    print("=== Testing Operation Modes ===")
    # 测试 NORMAL 模式
    bmm.operation_mode = bmm150.NORMAL
    print("Operation mode: %s" % bmm.operation_mode)
    time.sleep_ms(100)

    # 测试 FORCED 模式
    bmm.operation_mode = bmm150.FORCED
    print("Operation mode: %s" % bmm.operation_mode)
    time.sleep_ms(100)

    # 恢复 NORMAL 模式
    bmm.operation_mode = bmm150.NORMAL
    print("Restored to NORMAL mode")
    print()


def test_data_rates():
    """
    测试数据速率配置
    """
    print("=== Testing Data Rates ===")
    rates = [
        (bmm150.RATE_10HZ, "10Hz"),
        (bmm150.RATE_2HZ, "2Hz"),
        (bmm150.RATE_30HZ, "30Hz"),
    ]
    for rate_val, rate_name in rates:
        bmm.data_rate = rate_val
        print("Data rate set to: %s" % rate_name)
        print("Current data rate: %s" % bmm.data_rate)
        time.sleep_ms(100)
    print()


def test_thresholds():
    """
    测试阈值配置
    """
    print("=== Testing Thresholds ===")
    # 测试高阈值
    bmm.high_threshold = 100
    print("High threshold set to: %d" % bmm.high_threshold)

    # 测试低阈值
    bmm.low_threshold = 50
    print("Low threshold set to: %d" % bmm.low_threshold)
    print()


def test_interrupt_mode():
    """
    测试中断模式配置
    """
    print("=== Testing Interrupt Mode ===")
    # 启用中断
    bmm.interrupt_mode = bmm150.INT_ENABLED
    print("Interrupt mode: %s" % bmm.interrupt_mode)

    # 读取中断状态
    status = bmm.status_interrupt
    print("Interrupt status: %s" % str(status))
    print()


def print_continuous_data():
    """
    连续打印磁场数据（高频函数，供 REPL 手动调用）
    """
    magx, magy, magz, hall = bmm.measurements
    print("X: %d uT, Y: %d uT, Z: %d uT, Hall: %d" % (magx, magy, magz, hall))
    status = bmm.status_interrupt
    print("Interrupt status: %s" % str(status))
    print()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: Testing BMM150 Magnetometer Driver ...")

# 初始化 I2C 总线
i2c = I2C(I2C_BUS_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描 I2C 设备
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C devices found")
print("I2C devices found: %s" % [hex(addr) for addr in devices])

# 验证 BMM150 设备地址
if BMM150_DEFAULT_ADDR not in devices:
    raise RuntimeError("BMM150 not found at address 0x%02X" % BMM150_DEFAULT_ADDR)
print("BMM150 found at address: 0x%02X" % BMM150_DEFAULT_ADDR)

# 验证设备 ID
device_id = i2c.readfrom_mem(BMM150_DEFAULT_ADDR, BMM150_DEVICE_ID_REG, 1)[0]
if device_id != BMM150_EXPECTED_ID:
    raise RuntimeError("Invalid device ID: 0x%02X, expected 0x%02X" % (device_id, BMM150_EXPECTED_ID))
print("Device ID verified: 0x%02X" % device_id)

# 初始化 BMM150 驱动
bmm = bmm150.BMM150(i2c)
print("BMM150 driver initialized")
print()

# 执行初始化测试
test_basic_measurements()
test_operation_modes()
test_data_rates()
test_thresholds()
test_interrupt_mode()

print("=== Initialization tests completed ===")
print("Entering continuous monitoring mode...")
print()

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 低频查询：每 500ms 打印一次磁场数据
            magx, magy, magz, hall = bmm.measurements
            print("X: %d uT, Y: %d uT, Z: %d uT" % (magx, magy, magz))

            last_print_time = current_time

        # print_continuous_data()  # 高频函数，注释默认执行，可 REPL 手动调用
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    bmm.deinit()
    del bmm
    del i2c
    print("Program exited")

