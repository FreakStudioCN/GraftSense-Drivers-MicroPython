# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 SI4732 AM/FM 收音机接收器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from si4732 import SI4732

# ======================================== 全局变量 ============================================

# ==================== I2C 引脚配置（根据实际接线修改） ====================
I2C_CHANNEL = 0
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 100000

# ==================== 复位引脚配置（根据实际接线修改） ====================
RESET_PIN = 4

# ==================== 设备地址配置 ====================
# 0x63: SEN 引脚拉高（默认），0x11: SEN 引脚拉低
DEVICE_ADDRESS = 0x63

# ==================== 测试频率配置 ====================
# FM 测试频率（kHz）：101.7 MHz
TEST_FM_FREQ_KHZ = 101700

# 全局设备引用（用于 finally 块安全释放）
device = None

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing SI4732 AM/FM radio receiver driver...")

# 初始化 I2C 引脚
print("Initializing I2C pins...")
scl_pin = Pin(SCL_PIN)
sda_pin = Pin(SDA_PIN)

# 初始化 I2C 总线
print("Initializing I2C bus (freq=%dHz)...")
i2c = I2C(I2C_CHANNEL, scl=scl_pin, sda=sda_pin, freq=I2C_FREQ)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
print("I2C devices found: %s" % [hex(d) for d in devices])

if DEVICE_ADDRESS not in devices:
    raise RuntimeError("SI4732 not found on I2C bus at address 0x%02X. " "Check wiring and SEN pin level." % DEVICE_ADDRESS)

# 初始化复位引脚
print("Initializing reset pin...")
reset_pin = Pin(RESET_PIN, Pin.OUT)
reset_pin.value(1)

# 初始化 SI4732 驱动实例
print("Initializing SI4732 driver...")
device = SI4732(i2c, address=DEVICE_ADDRESS, reset_pin=reset_pin, debug=True)

# 硬件复位
print("Resetting SI4732...")
device.reset()

# 上电（FM 模式，模拟音频输出）
print("Powering up SI4732 in FM mode...")
device.power_up(SI4732.FUNC_FM)

# WHO_AM_I：读取芯片版本信息验证设备身份
print("Reading chip revision info...")
revision = device.get_revision()
print("Part number:       0x%02X" % revision["part_number"])
print("Firmware:          %d.%d" % (revision["firmware_major"], revision["firmware_minor"]))
print("Patch:             %d.%d" % (revision["patch_high"], revision["patch_low"]))
print("Component:         %d.%d" % (revision["component_major"], revision["component_minor"]))
print("Chip revision:     0x%02X" % revision["chip_revision"])

# 验证部件号（SI4732 的 part_number 通常为特定值）
# 注：不同 SI47xx 型号部件号不同，此处仅检查非零
if revision["part_number"] == 0 or revision["part_number"] == 0xFF:
    raise RuntimeError("SI4732 identity check failed: unexpected part_number=0x%02X" % revision["part_number"])

# FM 调谐测试
print("Tuning FM to %d kHz..." % TEST_FM_FREQ_KHZ)
device.fm_tune_freq(TEST_FM_FREQ_KHZ)
time.sleep_ms(200)

# 读取调谐状态
tune_status = device.get_tune_status()
print("Tune status:")
print("  Valid:      %s" % tune_status["valid"])
print("  Frequency:  %d" % tune_status["frequency"])
print("  RSSI:       %d" % tune_status["rssi"])
print("  SNR:        %d" % tune_status["snr"])
print("  Freq offset:%d" % tune_status["freq_offset"])

print("SI4732 initialized successfully.")

# ========================================  主程序  ===========================================

try:
    while True:
        # 示例循环：保持设备运行
        # 实际应用中可在此处执行频率切换、状态查询等操作
        time.sleep_ms(1000)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if device is not None:
        device.deinit()
    device = None
    print("Program exited")
