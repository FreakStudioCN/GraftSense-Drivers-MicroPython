# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午
# @Author  : hogeiha
# @File    : main.py
# @Description : VL53L5CX 8x8 多区域 ToF 距离传感器读取示例

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
from os import stat
from time import sleep
from vl53l5cx.mp import VL53L5CXMP
from vl53l5cx import DATA_DISTANCE_MM, DATA_TARGET_STATUS
from vl53l5cx import RESOLUTION_4X4, STATUS_VALID, STATUS_VALID_LARGE_PULSE

# ======================================== 全局变量 ============================================

# VL53L5CX 默认 I2C 地址
VL53L5CX_ADDR = 0x29

# I2C 数据线连接到 Pico GPIO4
I2C_SDA_PIN = 4

# I2C 时钟线连接到 Pico GPIO5
I2C_SCL_PIN = 5

# VL53L5CX LPn 复位引脚连接到 Pico GPIO6
LPN_PIN = 6

# VL53L5CX 推荐使用较高 I2C 频率
I2C_FREQ = 1000000

# 测距分辨率设置为 4x4
SENSOR_RESOLUTION = RESOLUTION_4X4

# 4x4 分辨率对应网格宽度
GRID_SIZE = 4

# 测距频率设置为 2Hz
RANGING_FREQ = 2

# VL53L5CX 固件资源文件路径
FIRMWARE_FILE = "vl53l5cx/vl_fw_config.bin"

# ======================================== 功能函数 ============================================


def print_distance_grid(distance, status, grid_size: int) -> None:
    """
    打印距离网格。
    Args:
        distance (list | tuple): 距离数据列表。
        status (list | tuple): 目标状态列表。
        grid_size (int): 网格边长。

    Raises:
        ValueError: 参数为空或网格非法时抛出。
        TypeError: 网格类型非法时抛出。

    Notes:
        无效测距点显示为 xxxx。

    ==========================================
    Print distance grid.
    Args:
        distance (list | tuple): Distance data list.
        status (list | tuple): Target status list.
        grid_size (int): Grid side length.

    Raises:
        ValueError: Raised when parameter is None or grid is invalid.
        TypeError: Raised when grid type is invalid.

    Notes:
        Invalid ranging points are shown as xxxx.
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

# ======================================== 初始化配置 ===========================================

sleep(3)
print("FreakStudio: VL53L5CX distance sensor")

# 检查固件资源文件是否存在
try:
    stat(FIRMWARE_FILE)
except OSError:
    raise SystemExit("Missing firmware file vl53l5cx/vl_fw_config.bin")

# 初始化 I2C 总线
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")

# 判断是否扫描到 I2C 设备
if len(devices_list) == 0:
    print("No i2c device")
    raise SystemExit("I2C scan found no devices")

# 判断是否扫描到 VL53L5CX 默认地址
if VL53L5CX_ADDR not in devices_list:
    print("VL53L5CX address not found")
    raise SystemExit("No VL53L5CX device found")

# 打印 VL53L5CX 地址
print("I2C hexadecimal address:", hex(VL53L5CX_ADDR))

# 初始化 LPn 复位控制引脚
lpn_pin = Pin(LPN_PIN, Pin.OUT, value=1)

# 创建 VL53L5CX 传感器对象
tof = VL53L5CXMP(i2c_bus, addr=VL53L5CX_ADDR, lpn=lpn_pin)

# 复位传感器
tof.reset()

# 检查传感器是否在线
if not tof.is_alive():
    raise SystemExit("VL53L5CX not detected")

# 初始化传感器固件和配置
tof.init()

# 设置测距分辨率
tof.resolution = SENSOR_RESOLUTION

# 设置测距频率
tof.ranging_freq = RANGING_FREQ

# 启动测距并启用距离和目标状态输出
tof.start_ranging({DATA_DISTANCE_MM, DATA_TARGET_STATUS})

# 打印测距启动提示
print("Start ranging")

# ========================================  主程序  ============================================

try:
    while True:
        # 检查是否有新的测距数据
        if tof.check_data_ready():
            # 读取测距结果
            results = tof.get_ranging_data()

            # 打印距离网格
            print_distance_grid(
                results.distance_mm,
                results.target_status,
                GRID_SIZE,
            )

        # 短暂延时以降低循环占用
        sleep(0.05)
except KeyboardInterrupt:
    # 停止测距
    tof.stop_ranging()

    # 打印停止提示
    print("Ranging stopped")
