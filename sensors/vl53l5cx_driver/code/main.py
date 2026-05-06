# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 09:00
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试VL53L5CX 8x8多区域ToF距离传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from os import stat
from vl53l5cx.mp import VL53L5CXMP
from vl53l5cx import DATA_DISTANCE_MM, DATA_TARGET_STATUS
from vl53l5cx import RESOLUTION_4X4, STATUS_VALID, STATUS_VALID_LARGE_PULSE

# ======================================== 全局变量 ============================================

VL53L5CX_ADDR = 0x29
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
LPN_PIN = 6
I2C_FREQ = 1_000_000
SENSOR_RESOLUTION = RESOLUTION_4X4
GRID_SIZE = 4
RANGING_FREQ = 2
FIRMWARE_FILE = "vl53l5cx/vl_fw_config.bin"

# ======================================== 功能函数 ============================================


def print_distance_grid(distance, status, grid_size: int) -> None:
    """
    打印距离网格，无效点显示为 xxxx
    Args:
        distance: 距离数据列表
        status: 目标状态列表
        grid_size (int): 网格边长
    Raises:
        ValueError: 参数为空或网格非法
        TypeError: grid_size 类型非法
    ==========================================
    Print distance grid; invalid points shown as xxxx.
    """
    if distance is None:
        raise ValueError("Distance cannot be None")
    if status is None:
        raise ValueError("Status cannot be None")
    if grid_size is None:
        raise ValueError("Grid size cannot be None")
    if not isinstance(grid_size, int):
        raise TypeError("Grid size must be integer")
    if grid_size <= 0:
        raise ValueError("Grid size must be greater than zero")

    for index, value in enumerate(distance):
        if status[index] in (STATUS_VALID, STATUS_VALID_LARGE_PULSE):
            print("{:4}".format(value), end=" ")
        else:
            print("xxxx", end=" ")
        if (index + 1) % grid_size == 0:
            print("")
    print("")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using VL53L5CX 8x8 multi-zone ToF distance sensor ...")

# 检查固件资源文件是否存在
try:
    stat(FIRMWARE_FILE)
except OSError:
    raise SystemExit("Missing firmware file: %s" % FIRMWARE_FILE)

# 初始化 I2C 总线
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")

if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")
print("I2C devices found: %d" % len(devices_list))

if VL53L5CX_ADDR not in devices_list:
    raise RuntimeError("VL53L5CX not found on I2C bus")
print("I2C address: %s" % hex(VL53L5CX_ADDR))

# 初始化 LPn 复位控制引脚
lpn_pin = Pin(LPN_PIN, Pin.OUT, value=1)

# 创建传感器对象
tof = VL53L5CXMP(i2c_bus, addr=VL53L5CX_ADDR, lpn=lpn_pin)

# 复位传感器
tof.reset()

# 检查传感器是否在线
if not tof.is_alive():
    raise RuntimeError("VL53L5CX not detected")
print("Sensor initialization successful")

# 初始化传感器固件和配置
tof.init()

# 设置测距分辨率和频率
tof.resolution = SENSOR_RESOLUTION
tof.ranging_freq = RANGING_FREQ

# 启动测距，启用距离和目标状态输出
tof.start_ranging({DATA_DISTANCE_MM, DATA_TARGET_STATUS})
print("Start ranging")

# ========================================  主程序  ===========================================

try:
    while True:
        # 检查是否有新的测距数据
        if tof.check_data_ready():
            results = tof.get_ranging_data()
            print_distance_grid(results.distance_mm, results.target_status, GRID_SIZE)
        time.sleep_ms(50)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    tof.deinit()
    del tof
    print("Program exited")
