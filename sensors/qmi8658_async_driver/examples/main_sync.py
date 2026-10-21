# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 QMI8658 驱动类代码
# @License : Apache-2.0

from machine import I2C, Pin
import time

# const() 兼容导入
try:
    from micropython import const
except ImportError:

    def const(value):
        return value


from qmi8658 import QMI8658

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# --- 硬件引脚配置 (请根据实际接线修改) ---
SCL_PIN = const(22)  # I2C 时钟引脚
SDA_PIN = const(21)  # I2C 数据引脚
I2C_FREQ = const(400000)  # I2C 总线频率 (Hz)
# 复位引脚 (不使用硬件复位时设为 -1)
RST_PIN = const(-1)

# --- QMI8658 设备常量 ---
QMI8658_DEFAULT_ADDR = const(0x6B)  # 默认 I2C 地址
QMI8658_WHO_AM_I_VALUE = const(0x05)  # 期望的芯片 ID
QMI8658_WHO_AM_I_REG = const(0x00)  # WHO_AM_I 寄存器地址

# 打印间隔控制
last_print_time = time.ticks_ms()
print_interval = 1000  # 打印间隔 (ms)

# ======================================== 功能函数 ============================================


def scan_i2c_bus(i2c):
    """扫描 I2C 总线，返回发现的设备地址列表"""
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    return devices


def verify_device(i2c, target_addr, expected_id, id_reg):
    """验证指定地址的设备芯片 ID"""
    try:
        chip_id = i2c.readfrom_mem(target_addr, id_reg, 1)[0]
    except OSError as e:
        raise RuntimeError("I2C read failed for WHO_AM_I at addr 0x%02X: %s" % (target_addr, str(e)))
    if chip_id != expected_id:
        raise RuntimeError("Device at 0x%02X has unexpected ID: expected 0x%02X, got 0x%02X" % (target_addr, expected_id, chip_id))
    return chip_id


def print_raw_data(data):
    """打印原始六轴数据 (格式化输出)"""
    print("Raw: ax=%6d  ay=%6d  az=%6d  |  gx=%6d  gy=%6d  gz=%6d" % (data[0], data[1], data[2], data[3], data[4], data[5]))


def print_converted_data(data):
    """打印转换后的六轴数据 (加速度 g, 陀螺仪 dps)"""
    print("Cvt: ax=%+7.3f  ay=%+7.3f  az=%+7.3f  |  gx=%+7.2f  gy=%+7.2f  gz=%+7.2f" % (data[0], data[1], data[2], data[3], data[4], data[5]))


# ======================================== 初始化配置 ===========================================

# 等待设备就绪
time.sleep(3)

print("FreakStudio: Testing QMI8658/QMI8658C 6-axis IMU driver")

# 初始化 I2C 总线
# 请根据实际接线修改 SCL/SDA 引脚号和 I2C 通道
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
print("I2C bus initialised: scl=%d, sda=%d, freq=%d Hz" % (SCL_PIN, SDA_PIN, I2C_FREQ))

# 扫描 I2C 总线
print("Scanning I2C bus...")
devices = scan_i2c_bus(i2c)
print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))

# 检查目标设备是否存在
if QMI8658_DEFAULT_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % QMI8658_DEFAULT_ADDR)
print("Device found at 0x%02X" % QMI8658_DEFAULT_ADDR)

# 验证芯片 ID
chip_id = verify_device(i2c, QMI8658_DEFAULT_ADDR, QMI8658_WHO_AM_I_VALUE, QMI8658_WHO_AM_I_REG)
print("WHO_AM_I verified: 0x%02X" % chip_id)

# 创建驱动实例
# 复位引脚：若 RST_PIN >= 0 则使用引脚对象，否则不使用硬件复位
if RST_PIN >= 0:
    rst = Pin(RST_PIN, Pin.OUT)
    imu = QMI8658(i2c, reset_pin=rst, debug=False)
    print("QMI8658 initialised (with hardware reset pin %d)" % RST_PIN)
else:
    imu = QMI8658(i2c, debug=False)
    print("QMI8658 initialised (no hardware reset)")

# 读取芯片信息
rev = imu.revision()
print("Chip revision: 0x%02X" % rev)
print("Device ready, entering data loop...")
print("")

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        # 按设定的间隔打印数据
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取并打印原始数据
            raw = imu.read_raw()
            print_raw_data(raw)
            # 读取并打印转换后的数据
            converted = imu.read_xyz()
            print_converted_data(converted)
            print("")
            last_print_time = current_time
        # 短暂延时，避免占用过多 CPU
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    imu.deinit()
    del imu
    print("Program exited")
