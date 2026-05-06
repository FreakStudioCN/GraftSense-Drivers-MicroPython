# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 17:30
# @Author  : goctaprog
# @File    : main.py
# @Description : Test code for HSCDTD008A geomagnetic sensor driver
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
import math
import sys
from machine import Pin, SoftI2C
import hscdtd008a
from sensor_pack.bus_service import I2cAdapter

# ======================================== 全局变量 ============================================

# I2C 引脚与频率配置
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400_000

# 目标传感器 I2C 地址列表
TARGET_SENSOR_ADDRS = [0x0C]

# 期望的芯片 ID（用于 ID 验证）
EXPECTED_CHIP_ID = 0x49

# 测量循环参数
MEAS_DELAY_MS = 250
MEAS_MAX_COUNT = 30

# ======================================== 功能函数 ============================================

def show_state(sen: hscdtd008a.HSCDTD008A) -> None:
    """打印传感器当前工作模式状态"""
    print("in standby mode: %s; hi_dynamic_range: %s" % (sen.in_standby_mode(), sen.hi_dynamic_range))
    print("single meas mode: %s; continuous meas mode: %s" % (sen.is_single_meas_mode(), sen.is_continuous_meas_mode()))


def test_temperature(sen: hscdtd008a.HSCDTD008A, count: int = MEAS_MAX_COUNT) -> None:
    """测试温度测量功能，循环读取 count 次"""
    sen.enable_temp_meas(True)
    print("--- Temperature measurement test ---")
    show_state(sen)
    print(16 * "_")
    cnt = 0
    while cnt < count:
        status = sen.get_status()
        # 检查温度数据就绪标志（TRDY，bit1）
        if status[3]:
            temp = sen.get_temperature()
            print("Sensor temperature: %d C" % temp)
            # 重新触发下一次温度测量
            sen.enable_temp_meas(True)
        else:
            print("status: %s" % str(status))
        time.sleep_ms(MEAS_DELAY_MS)
        cnt += 1


def test_force_mode(sen: hscdtd008a.HSCDTD008A, count: int = MEAS_MAX_COUNT) -> None:
    """测试单次（Force）测量模式，循环读取 count 次"""
    print("--- Magnetic field measurement: Force mode ---")
    show_state(sen)
    print(16 * "_")
    # 启动单次测量模式
    sen.start_measure(continuous_mode=False)
    cnt = 0
    while cnt < count:
        status = sen.get_status()
        # 检查数据就绪（DRDY）或数据溢出（DOR）标志
        if status[0] or status[1]:
            field = sen.get_axis(-1)
            # 触发下一次单次测量
            sen.start_measure(continuous_mode=False)
            print("magnetic field: X:%d Y:%d Z:%d" % (field[0], field[1], field[2]))
        else:
            print("status: %s" % str(status))
        time.sleep_ms(MEAS_DELAY_MS)
        cnt += 1


def test_continuous_mode(sen: hscdtd008a.HSCDTD008A, count: int = MEAS_MAX_COUNT) -> None:
    """测试周期（Continuous）测量模式，循环读取 count 次，叠加偏移量"""
    print("--- Magnetic field measurement: Continuous mode ---")
    # 启用偏移量叠加
    sen.use_offset = True
    sen.start_measure(continuous_mode=True)
    cnt = 0
    while cnt < count:
        status = sen.get_status()
        # 检查数据就绪标志（DRDY）
        if status[0]:
            field = sen.get_axis(-1)
            # 计算合磁场强度（三轴平方和开根号）
            mag_strength = math.sqrt(field[0] ** 2 + field[1] ** 2 + field[2] ** 2)
            print("magnetic field: X:%d Y:%d Z:%d strength:%.2f" % (field[0], field[1], field[2], mag_strength))
        time.sleep_ms(MEAS_DELAY_MS)
        cnt += 1

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: HSCDTD008A geomagnetic sensor test starting ...")

# 初始化 I2C 总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线，检查设备是否存在
devices_list = i2c_bus.scan()
print("I2C scan result: %s" % [hex(d) for d in devices_list])

if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")

# 在扫描结果中查找目标传感器地址
sensor = None
for device_addr in devices_list:
    if device_addr in TARGET_SENSOR_ADDRS:
        print("Target sensor found at address: %s" % hex(device_addr))
        adapter = I2cAdapter(i2c_bus)
        sensor = hscdtd008a.HSCDTD008A(adapter)
        break

if sensor is None:
    raise RuntimeError("Target sensor not found on I2C bus")

# 读取并验证芯片 ID
chip_id = sensor.get_id()
print("Chip ID: %s (expected: %s)" % (hex(chip_id), hex(EXPECTED_CHIP_ID)))
if chip_id != EXPECTED_CHIP_ID:
    raise RuntimeError("Chip ID mismatch: got %s, expected %s" % (hex(chip_id), hex(EXPECTED_CHIP_ID)))

# 打印初始偏移量
print("Offset drift values: %s" % str(sensor.offset_drift_values))
print(16 * "_")
show_state(sensor)
print(16 * "_")

# 执行自检（必须在激活模式下）
sensor.start_measure(active_pwr_mode=True)
test_result = sensor.perform_self_test()
if not test_result:
    print("Sensor self-test FAILED: broken sensor or invalid mode")
    sys.exit(1)
print("Sensor self-test passed")

# ========================================  主程序  ===========================================

try:
    while True:
        # 依次执行三类测试场景
        test_temperature(sensor)
        print(16 * "_")
        test_force_mode(sensor)
        print(16 * "_")
        test_continuous_mode(sensor)
        print(16 * "_")
        # 所有测试完成后退出循环
        break

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
