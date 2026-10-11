try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2023/01/01 00:00
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 BMM150 三轴磁力计驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
from machine import Pin, I2C
import time
from micropython_bmm150 import bmm150
from bmm150_async import BMM150Async

# ======================================== 全局变量 ============================================
# I2C 配置常量
I2C_BUS_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000

# BMM150 设备常量
BMM150_DEVICE_ID_REG = 0xFF
BMM150_EXPECTED_ID = 0x32
BMM150_DEFAULT_ADDR = 0x13

# 打印间隔（毫秒）
print_interval = 500
last_print_time = 0

# ======================================== 功能函数 ============================================
async def test_basic_measurements():
    """
    测试基本磁场测量功能
    """
    print("=== Testing Basic Measurements ===")
    magx, magy, magz, hall = await bmm.get_measurements_async()
    print("X-axis: %d uT" % magx)
    print("Y-axis: %d uT" % magy)
    print("Z-axis: %d uT" % magz)
    print("Hall resistance: %d" % hall)
    print()


async def test_operation_modes():
    """
    测试操作模式切换
    """
    print("=== Testing Operation Modes ===")
    # 测试 NORMAL 模式
    await bmm.set_operation_mode_async(bmm150.NORMAL)
    print("Operation mode: %s" % await bmm.get_operation_mode_async())
    await asyncio.sleep_ms(100)

    # 测试 FORCED 模式
    await bmm.set_operation_mode_async(bmm150.FORCED)
    print("Operation mode: %s" % await bmm.get_operation_mode_async())
    await asyncio.sleep_ms(100)

    # 恢复 NORMAL 模式
    await bmm.set_operation_mode_async(bmm150.NORMAL)
    print("Restored to NORMAL mode")
    print()


async def test_data_rates():
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
        await bmm.set_data_rate_async(rate_val)
        print("Data rate set to: %s" % rate_name)
        print("Current data rate: %s" % await bmm.get_data_rate_async())
        await asyncio.sleep_ms(100)
    print()


async def test_thresholds():
    """
    测试阈值配置
    """
    print("=== Testing Thresholds ===")
    # 测试高阈值
    await bmm.set_high_threshold_async(100)
    print("High threshold set to: %d" % await bmm.get_high_threshold_async())

    # 测试低阈值
    await bmm.set_low_threshold_async(50)
    print("Low threshold set to: %d" % await bmm.get_low_threshold_async())
    print()


async def test_interrupt_mode():
    """
    测试中断模式配置
    """
    print("=== Testing Interrupt Mode ===")
    # 启用中断
    await bmm.set_interrupt_mode_async(bmm150.INT_ENABLED)
    print("Interrupt mode: %s" % await bmm.get_interrupt_mode_async())

    # 读取中断状态
    status = await bmm.get_status_interrupt_async()
    print("Interrupt status: %s" % str(status))
    print()


async def print_continuous_data():
    """
    连续打印磁场数据（高频函数，供 REPL 手动调用）
    """
    magx, magy, magz, hall = await bmm.get_measurements_async()
    print("X: %d uT, Y: %d uT, Z: %d uT, Hall: %d" % (magx, magy, magz, hall))
    status = await bmm.get_status_interrupt_async()
    print("Interrupt status: %s" % str(status))
    print()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

async def main():
    global bmm
    i2c = None
    bmm = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Testing BMM150 Magnetometer Driver ...")
    try:
        i2c = I2C(I2C_BUS_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C devices found")
        print("I2C devices found: %s" % [hex(addr) for addr in devices])
        if BMM150_DEFAULT_ADDR not in devices:
            raise RuntimeError("BMM150 not found at address 0x%02X" % BMM150_DEFAULT_ADDR)
        bmm = BMM150Async(i2c, BMM150_DEFAULT_ADDR)
        print("BMM150 driver initialized")
        await test_basic_measurements()
        await test_operation_modes()
        await test_data_rates()
        await test_thresholds()
        await test_interrupt_mode()
        print("=== Initialization tests completed ===")
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= print_interval:
                magx, magy, magz, hall = await bmm.get_measurements_async()
                print("X: %d uT, Y: %d uT, Z: %d uT" % (magx, magy, magz))
                last_print_time = current_time
            await asyncio.sleep_ms(10)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as error:
        print("Hardware communication error: %s" % error)
        raise
    finally:
        print("Cleaning up resources...")
        if bmm is not None:
            await bmm.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()
        print("Program exited")
# ======================================== 主程序 ==============================================
asyncio.run(main())
