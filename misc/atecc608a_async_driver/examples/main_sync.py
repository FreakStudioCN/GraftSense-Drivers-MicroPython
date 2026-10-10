# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 ATECC608A 加密认证芯片驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import machine
import time
import ubinascii
from atecc608a import ATECC608A

# ======================================== 全局变量 ============================================

# I2C 硬件引脚配置（ESP32 示例，可按实际接线修改）
I2C_BUS = 0
PIN_SCL = 22
PIN_SDA = 21
I2C_FREQ = 1000000

# ATECC608A I2C 默认地址
DEVICE_ADDR = 0x60

# ATECC608A 设备类型标识字节（位于 info 响应字节 3）
ATCAB_INFO_DEVTYPE_INDEX = 3
ATCAB_INFO_DEVTYPE_ECC608A = 0x60

# 测试数据包
TEST_DATA = b"Hello ATECC608A!"

# 定时打印间隔（ms）
last_print_time = 0
print_interval = 3000

# ======================================== 功能函数 ============================================


def test_device_info(device):
    """打印设备信息（低频，保留自动执行）"""
    try:
        # 读取设备信息（revision 模式）
        info = device.atcab_info().response_data
        rev = ubinascii.hexlify(info)
        print("Device info: %s" % rev)
    except Exception as e:
        print("Failed to read device info: %s" % str(e))


def test_serial_number(device):
    """打印芯片序列号（低频，保留自动执行）"""
    try:
        # 读取序列号（config zone 前 32 字节含 SN）
        sn_packet = device.atcab_read_serial_number()
        sn = ubinascii.hexlify(sn_packet.response_data)
        print("Serial number: %s" % sn)
    except Exception as e:
        print("Failed to read serial number: %s" % str(e))


def test_random(device):
    """生成随机数（高频，默认注释调用，可 REPL 手动调用）"""
    try:
        rnd_packet = device.atcab_random()
        rnd = ubinascii.hexlify(rnd_packet.response_data)
        print("Random: %s" % rnd)
    except Exception as e:
        print("Failed to generate random: %s" % str(e))


def test_sha256(device, data: bytes = TEST_DATA):
    """SHA-256 计算（高频，默认注释调用，可 REPL 手动调用）"""
    try:
        sha_packet = device.atcab_sha(data)
        # SHA 响应数据包含 32 字节摘要
        digest = ubinascii.hexlify(sha_packet.response_data)
        print("SHA-256: %s" % digest)
    except Exception as e:
        print("Failed to compute SHA-256: %s" % str(e))


def test_read_config_zone(device):
    """读取配置区数据（低频，默认注释调用，可 REPL 手动调用）"""
    try:
        config_packet = device.atcab_read_config_zone()
        config = ubinascii.hexlify(config_packet.response_data)
        print("Config zone: %s" % config)
    except Exception as e:
        print("Failed to read config zone: %s" % str(e))


def test_check_lock_status(device):
    """检查各区锁定状态（低频，保留自动执行）"""
    try:
        # 检查配置区是否已锁定
        config_locked = device.atcab_is_locked("config")
        print("Config zone locked: %s" % config_locked)
        # 检查数据区是否已锁定
        data_locked = device.atcab_is_locked("data")
        print("Data zone locked: %s" % data_locked)
    except Exception as e:
        print("Failed to check lock status: %s" % str(e))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Testing ATECC608A crypto driver")

# 初始化 I2C 总线
print("Initializing I2C bus %d (SCL=%d, SDA=%d, freq=%d)..." % (I2C_BUS, PIN_SCL, PIN_SDA, I2C_FREQ))
i2c = machine.I2C(I2C_BUS, scl=machine.Pin(PIN_SCL), sda=machine.Pin(PIN_SDA), freq=I2C_FREQ)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))

# 检查是否未找到任何设备
if not devices:
    raise RuntimeError("No I2C device found")

# 检查目标地址设备是否存在
if DEVICE_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02x" % DEVICE_ADDR)

# 创建 ATECC608A 驱动实例
print("Initializing ATECC608A at address 0x%02x..." % DEVICE_ADDR)
device = ATECC608A(bus=i2c, address=DEVICE_ADDR, debug=False)
print("Device type: %s" % device.device)

# 验证设备类型
info_data = device.atcab_info().response_data
dev_type = info_data[ATCAB_INFO_DEVTYPE_INDEX]
if dev_type == ATCAB_INFO_DEVTYPE_ECC608A:
    print("Device verification: ATECC608A confirmed")
else:
    print("Device verification: unknown type 0x%02x" % dev_type)

# 版本信息
print("CryptoAuthLib version: %s" % device.atcab_version())

print("ATECC608A initialization successful!")

# ========================================  主程序  ===========================================

last_print_time = time.ticks_ms()

try:
    # 启动测试：读取设备信息和序列号
    print("\n--- Device Identification ---")
    test_device_info(device)
    test_serial_number(device)

    # 检查锁定状态
    print("\n--- Lock Status ---")
    test_check_lock_status(device)

    main_loop_count = 0
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            main_loop_count += 1
            print("\n--- Main loop #%d ---" % main_loop_count)

            # 低频自动执行：随机数生成
            print("Generating random number...")
            test_random(device)

            # 低频自动执行：SHA-256 测试
            print("Computing SHA-256...")
            test_sha256(device)

            # 配置区读取（数据量大，默认注释，可 REPL 手动调用）
            # test_read_config_zone(device)

            last_print_time = current_time

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    try:
        device.deinit()
    except Exception:
        pass
    del device
    print("Program exited")
