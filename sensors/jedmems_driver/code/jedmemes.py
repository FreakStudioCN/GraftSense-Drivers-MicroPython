# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/8 15:00
# @Author  : 侯钧瀚
# @File    : air_quality.py
# @Description : 基于MEMS气体传感器的空气质量监测模块驱动 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================
#导入常量模块
from micropython import const

# 导入时间模块
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class MEMSGasSensor:
    """
    MEMSGasSensor 类，用于通过 I2C 操作 MEMS 数字气体传感器，支持多种气体类型的浓度读取与零点校准。

    Attributes:
        i2c: I2C 实例，用于与传感器通信。
        addr (int): 传感器 I2C 地址。
        sensor_type (int): 传感器类型。

    Methods:
        __init__(i2c, sensor_type, addr7=MEMS_SENSOR_ADDR7): 初始化传感器。
        read_concentration(retries=3): 读取气体浓度。
        calibrate_zero(baseline_value, retries=3): 零点校准。

    ===========================================

    MEMSGasSensor driver class for MEMS digital gas sensor via I2C.
    Supports concentration reading and zero calibration.

    Attributes:
        i2c: I2C instance for communication.
        addr (int): Sensor I2C address.
        sensor_type (int): Sensor type.

    Methods:
        __init__(i2c, sensor_type, addr7=MEMS_SENSOR_ADDR7): Initialize sensor.
        read_concentration(retries=3): Read gas concentration.
        calibrate_zero(baseline_value, retries=3): Zero calibration.
    """
    OP_DELAY_MS = const(20)
    RESTART_DELAY_MS = const(5000)

    def __init__(self, i2c, addr7=0x2A):
        """
        初始化 MEMS 传感器实例。

        Args:
            i2c (I2C): I2C 实例。
            sensor_type (int): 传感器类型（如 VOC，CO，HCHO）。
            addr7 (int): 7 位地址（默认 0x2A）。

        ==========================================

        Initialize MEMS sensor instance.

        Args:
            i2c (I2C): I2C instance.
            sensor_type (int): Sensor type (e.g. VOC, CO, HCHO).
            addr7 (int): 7-bit address (default 0x2A).
        """
        self.i2c = i2c
        self.addr = addr7

    def read_concentration(self, retries=3):
        """
        读取气体浓度值。

        Args:
            retries (int): 失败时重试次数。

        Returns:
            int: 浓度值，或 None 如果读取失败。

        ==========================================

        Read the gas concentration value.

        Args:
            retries (int): Number of retries on failure.

        Returns:
            int: Concentration value, or None if failed.
        """
        for _ in range(retries):
            try:
                self.i2c.writeto(self.addr, bytearray([0xA1]))
                time.sleep_ms(OP_DELAY_MS)
                data = self.i2c.readfrom(self.addr, 2)
                concentration = data[0] * 256 + data[1]
                return concentration
            except Exception as e:
                print("Read failed:", e)
        return None

    def calibrate_zero(self, baseline_value, retries=3):
        """
        校准传感器零点。

        Args:
            baseline_value (int): 基线值。
            retries (int): 失败时重试次数。

        Returns:
            bool: 校准是否成功。

        ==========================================

        Calibrate sensor zero.

        Args:
            baseline_value (int): Baseline value.
            retries (int): Number of retries on failure.

        Returns:
            bool: Whether calibration is successful.
        """
        for _ in range(retries):
            try:
                self.i2c.writeto(self.addr, bytearray([0x32, baseline_value >> 8, baseline_value & 0xFF]))
                time.sleep_ms(OP_DELAY_MS)
                return True
            except Exception as e:
                print("Calibration failed:", e)
        return False

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
