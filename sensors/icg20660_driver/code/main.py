# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 ICG20660 驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from icg20660 import (
    ICG20660,
    GYRO_DLPF_DISABLED,
    GYRO_DLPF_ENABLED,
    DLPF_CFG_0,
    DLPF_CFG_1,
    DLPF_CFG_2,
    DLPF_CFG_7,
    FS_125_DPS,
    FS_500_DPS,
    RANGE_2G,
    RANGE_16G,
)

# ======================================== 全局变量 ============================================
print_interval = 2000  # 打印间隔（ms）

# I2C 设备验证常量
ICG20660_DEFAULT_ADDR = 0x69
ICG20660_WHO_AM_I_REG = 0x75
ICG20660_EXPECTED_ID = 0x91


# ======================================== 功能函数 ============================================
def print_device_status(icg):
    """打印设备当前配置状态（低频，默认注释调用，可 REPL 手动查看）"""
    print("--- Device Status ---")
    print("Gyro DLPF mode: %s" % icg.gyro_dlpf_mode)
    print("Gyro DLPF config: %s" % icg.gyro_dlpf_configuration)
    print("Gyro full scale: %s" % icg.gyro_full_scale)
    print("Accel range: %s" % icg.acceleration_range)
    print("Data rate: %.1f Hz" % icg.data_rate)
    print("---------------------")


def test_gyro_full_scale_boundary(icg):
    """测试陀螺仪满量程边界值（边界参数场景，默认注释，可 REPL 手动调用）"""
    print("=== Boundary: Gyro Full Scale ===")
    # 最小满量程 125 DPS
    icg.gyro_full_scale = FS_125_DPS
    print("Set FS_125_DPS: %s" % icg.gyro_full_scale)
    # 最大满量程 500 DPS
    icg.gyro_full_scale = FS_500_DPS
    print("Set FS_500_DPS: %s" % icg.gyro_full_scale)
    # 恢复默认
    icg.gyro_full_scale = FS_125_DPS


def test_accel_range_boundary(icg):
    """测试加速度计量程边界值（边界参数场景，默认注释，可 REPL 手动调用）"""
    print("=== Boundary: Accel Range ===")
    # 最小量程 2G
    icg.acceleration_range = RANGE_2G
    print("Set RANGE_2G: %s" % icg.acceleration_range)
    # 最大量程 16G
    icg.acceleration_range = RANGE_16G
    print("Set RANGE_16G: %s" % icg.acceleration_range)
    # 恢复默认
    icg.acceleration_range = RANGE_2G


def test_data_rate_boundary(icg):
    """测试采样率边界值（边界参数场景，默认注释，可 REPL 手动调用）"""
    print("=== Boundary: Data Rate ===")
    # 最高采样率 500 Hz
    icg.data_rate = 500.0
    print("Set 500.0 Hz: %.1f Hz" % icg.data_rate)
    # 最低采样率 3.9 Hz
    icg.data_rate = 3.9
    print("Set 3.9 Hz: %.1f Hz" % icg.data_rate)
    # 恢复默认
    icg.data_rate = 100.0


def test_exception_params(icg):
    """测试异常参数处理（异常参数场景，默认注释，可 REPL 手动调用）"""
    print("=== Exception: Invalid Parameters ===")

    # 非法陀螺仪满量程
    try:
        icg.gyro_full_scale = 99
    except ValueError as e:
        print("Caught expected: %s" % e)

    # 非法加速度计量程
    try:
        icg.acceleration_range = 10
    except ValueError as e:
        print("Caught expected: %s" % e)

    # 非法采样率
    try:
        icg.data_rate = 999.0
    except ValueError as e:
        print("Caught expected: %s" % e)

    # 非法 DLPF 配置
    try:
        icg.gyro_dlpf_configuration = 0b101
    except ValueError as e:
        print("Caught expected: %s" % e)


def test_dlpf_modes(icg):
    """测试 DLPF 模式切换（模式切换，默认注释，可 REPL 手动调用）"""
    print("=== DLPF Mode Switch ===")
    # 禁用 DLPF
    icg.gyro_dlpf_mode = GYRO_DLPF_DISABLED
    print("DLPF disabled: %s" % icg.gyro_dlpf_mode)
    # 启用 DLPF
    icg.gyro_dlpf_mode = GYRO_DLPF_ENABLED
    print("DLPF enabled: %s" % icg.gyro_dlpf_mode)
    # 切换带宽配置
    for cfg in (DLPF_CFG_0, DLPF_CFG_1, DLPF_CFG_2, DLPF_CFG_7):
        icg.gyro_dlpf_configuration = cfg
        print("DLPF config %s: %s" % (cfg, icg.gyro_dlpf_configuration))


# ======================================== 自定义类 ============================================
# 无自定义类

# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: Testing ICG20660 6-axis Gyro/Accel Driver ...")

last_print_time = time.ticks_ms()

# 初始化 I2C 总线（引脚按实际接线调整）
i2c = I2C(0, scl=Pin(5), sda=Pin(4))

# I2C 总线扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 检查目标设备是否在总线上
if ICG20660_DEFAULT_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % ICG20660_DEFAULT_ADDR)

# 创建传感器实例
icg = ICG20660(i2c, address=ICG20660_DEFAULT_ADDR)

# 验证设备 ID（WHO_AM_I 寄存器）
try:
    device_id = i2c.readfrom_mem(ICG20660_DEFAULT_ADDR, ICG20660_WHO_AM_I_REG, 1)[0]
    if device_id == ICG20660_EXPECTED_ID:
        print("Device found: ICG20660 (ID=0x%02X)" % device_id)
    else:
        print("Device not found: unexpected ID 0x%02X (expected 0x%02X)" % (device_id, ICG20660_EXPECTED_ID))
except OSError as e:
    raise RuntimeError("I2C communication failed during ID check") from e

# 打印初始配置
print_device_status(icg)

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()

        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取加速度数据（低频自动执行）
            accx, accy, accz = icg.acceleration
            print("Accel  | x: %7.2f  y: %7.2f  z: %7.2f  (m/s²)" % (accx, accy, accz))

            # 读取陀螺仪数据（低频自动执行）
            gx, gy, gz = icg.gyro
            print("Gyro   | x: %7.2f  y: %7.2f  z: %7.2f  (°/s)" % (gx, gy, gz))

            last_print_time = current_time

        # 模式切换测试函数（默认注释，可 REPL 手动调用）
        # test_gyro_full_scale_boundary(icg)
        # test_accel_range_boundary(icg)
        # test_data_rate_boundary(icg)
        # test_dlpf_modes(icg)
        # test_exception_params(icg)
        # print_device_status(icg)

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    icg.deinit()
    del icg
    print("Program exited")
