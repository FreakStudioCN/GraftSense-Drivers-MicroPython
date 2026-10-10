# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/15 下午3:30
# @Author  : Jose D. Montoya
# @File    : mmc5983.py
# @Description : MMC5983磁力计MicroPython驱动，提供磁场和温度测量功能
# @License : MIT
__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const
from micropython_mmc5983.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass

# ======================================== 全局变量 ============================================

# 器件标识寄存器地址
_REG_WHOAMI = const(0x2F)
# 数据寄存器起始地址
_DATA = const(0x00)
# 内部控制寄存器0地址
_INTERNAL_CONTROL0 = const(0x09)
# 内部控制寄存器1地址
_INTERNAL_CONTROL1 = const(0x0A)
# 内部控制寄存器2地址
_INTERNAL_CONTROL2 = const(0x0B)

# 操作模式常量
ONE_SHOT = const(0b0)  # 单次测量模式
CONTINUOUS = const(0b1)  # 连续测量模式
operation_mode_values = (ONE_SHOT, CONTINUOUS)

# 缩放因子常量
SCALE_FACTOR = const(16384)

# 连续模式频率常量
CM_OFF = const(0b000)  # 关闭连续模式
CM_1HZ = const(0b001)  # 1Hz
CM_10HZ = const(0b010)  # 10Hz
CM_20HZ = const(0b011)  # 20Hz
CM_50HZ = const(0b100)  # 50Hz
CM_100HZ = const(0b101)  # 100Hz
CM_200HZ = const(0b110)  # 200Hz
CM_1000HZ = const(0b111)  # 1000Hz
continuous_mode_frequency_values = (
    CM_OFF,
    CM_1HZ,
    CM_10HZ,
    CM_20HZ,
    CM_50HZ,
    CM_100HZ,
    CM_200HZ,
    CM_1000HZ,
)

# 带宽常量
BW_100HZ = const(0b00)  # 100Hz带宽
BW_200HZ = const(0b01)  # 200Hz带宽
BW_400HZ = const(0b10)  # 400Hz带宽
BW_800HZ = const(0b11)  # 800Hz带宽
bandwidth_values = (BW_100HZ, BW_200HZ, BW_400HZ, BW_800HZ)
# 对应带宽的延迟时间(秒)
delay_times = (0.008, 0.004, 0.002, 0.00005)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MMC5983:
    """
    MMC5983磁力计驱动类，通过I2C接口进行磁场和温度测量。

    Attributes:
        _i2c (I2C): I2C总线对象
        _address (int): 设备I2C地址，默认0x30
        _om_cached (int): 操作模式缓存值
        _cmfc (int): 连续模式频率缓存值
        _bw_cached (int): 带宽缓存值
        _device_id (RegisterStruct): 器件标识寄存器结构
        _raw_data (RegisterStruct): 原始磁场数据寄存器结构(3个半字+1字节)
        _temperature (RegisterStruct): 温度数据寄存器结构(1字节)
        _bandwidth (CBits): 带宽控制位字段(2位)
        _continuous_mode_frequency (CBits): 连续模式频率控制位字段(3位)
        _operation_mode (CBits): 操作模式控制位字段(1位)
        _start_magnetic_measure (CBits): 启动磁场测量控制位(1位)
        _start_temperature_measure (CBits): 启动温度测量控制位(1位)

    Methods:
        operation_mode(): 设置/获取操作模式(单次/连续)
        continuous_mode_frequency(): 设置/获取连续测量频率
        bandwidth(): 设置/获取带宽
        magnetic(): 读取磁场强度(微特斯拉)
        temperature(): 读取温度值(摄氏度)

    Notes:
        基于I2C通信，支持单次和连续测量模式，测量前需配置连续模式频率和带宽。

    ==========================================
    Driver class for MMC5983 magnetometer via I2C.

    Attributes:
        _i2c (I2C): I2C bus object
        _address (int): I2C device address, default 0x30
        _om_cached (int): Cached operation mode value
        _cmfc (int): Cached continuous mode frequency value
        _bw_cached (int): Cached bandwidth value
        _device_id (RegisterStruct): Device ID register structure
        _raw_data (RegisterStruct): Raw magnetic data register structure (3 half-words + 1 byte)
        _temperature (RegisterStruct): Temperature data register structure (1 byte)
        _bandwidth (CBits): Bandwidth control bit field (2 bits)
        _continuous_mode_frequency (CBits): Continuous mode frequency control bit field (3 bits)
        _operation_mode (CBits): Operation mode control bit field (1 bit)
        _start_magnetic_measure (CBits): Start magnetic measurement control bit (1 bit)
        _start_temperature_measure (CBits): Start temperature measurement control bit (1 bit)

    Methods:
        operation_mode(): Get/set operation mode (single-shot/continuous)
        continuous_mode_frequency(): Get/set continuous measurement frequency
        bandwidth(): Get/set bandwidth
        magnetic(): Read magnetic field strength (microteslas)
        temperature(): Read temperature value (Celsius)

    Notes:
        I2C-based communication, supports single-shot and continuous modes.
        Must configure continuous mode frequency and bandwidth before measurement.
    """

    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _raw_data = RegisterStruct(_DATA, "HHHB")
    _temperature = RegisterStruct(0x07, "B")

    _bandwidth = CBits(2, _INTERNAL_CONTROL1, 0)

    _continuous_mode_frequency = CBits(3, _INTERNAL_CONTROL2, 0)
    _operation_mode = CBits(1, _INTERNAL_CONTROL2, 3)

    _start_magnetic_measure = CBits(1, _INTERNAL_CONTROL0, 0)
    _start_temperature_measure = CBits(1, _INTERNAL_CONTROL0, 1)

    def __init__(self, i2c, address: int = 0x30) -> None:
        """
        初始化MMC5983传感器，配置I2C接口并设置默认工作模式。

        Args:
            i2c (I2C): 已初始化的machine.I2C对象
            address (int): 设备I2C地址，取值范围0x30或0x38，默认0x30

        Raises:
            RuntimeError: 无法找到MMC5983设备(器件ID不匹配)

        Notes:
            默认设置为连续模式、1Hz采样率、100Hz带宽。

        ==========================================
        Initialize MMC5983 sensor, configure I2C interface and set default operation mode.

        Args:
            i2c (I2C): Initialized machine.I2C object
            address (int): I2C device address, valid values 0x30 or 0x38, default 0x30

        Raises:
            RuntimeError: Failed to find MMC5983 device (device ID mismatch)

        Notes:
            Default settings: continuous mode, 1Hz sampling rate, 100Hz bandwidth.
        """
        self._i2c = i2c
        self._address = address

        # 检查器件ID
        if self._device_id != 0x30:
            raise RuntimeError("Failed to find MMC5983")

        # 设置默认工作参数
        self.operation_mode = CONTINUOUS
        self.continuous_mode_frequency = CM_1HZ
        self.bandwidth = BW_100HZ

    @property
    def operation_mode(self) -> str:
        """
        获取当前操作模式字符串描述。

        Returns:
            str: 操作模式字符串，'ONE_SHOT'或'CONTINUOUS'

        Notes:
            进入连续模式前必须设置有效的连续模式频率(非CM_OFF)。

        ==========================================
        Get current operation mode as string.

        Returns:
            str: Operation mode string, 'ONE_SHOT' or 'CONTINUOUS'

        Notes:
            Must set a valid continuous mode frequency (non-CM_OFF) before entering continuous mode.
        """
        values = ("ONE_SHOT", "CONTINUOUS")
        return values[self._om_cached]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        """
        设置操作模式。

        Args:
            value (int): 操作模式常量，必须为ONE_SHOT或CONTINUOUS

        Raises:
            ValueError: value无效或连续模式频率为CM_OFF

        ==========================================
        Set operation mode.

        Args:
            value (int): Operation mode constant, must be ONE_SHOT or CONTINUOUS

        Raises:
            ValueError: value is invalid or continuous mode frequency is CM_OFF
        """
        if value not in operation_mode_values:
            raise ValueError("Value must be a valid operation_mode setting")
        if self._continuous_mode_frequency == 0:
            raise ValueError("Please select first a valid continuous mode frequency")
        self._operation_mode = value
        self._om_cached = value

    @property
    def continuous_mode_frequency(self) -> str:
        """
        获取连续模式频率字符串描述。

        Returns:
            str: 频率模式字符串，如'CM_1HZ'、'CM_10HZ'等

        Notes:
            实际频率基于带宽为BW_100HZ的假设。

        ==========================================
        Get continuous mode frequency as string.

        Returns:
            str: Frequency mode string, e.g. 'CM_1HZ', 'CM_10HZ', etc.

        Notes:
            Actual frequency assumes bandwidth is BW_100HZ.
        """
        values = (
            "CM_OFF",
            "CM_1HZ",
            "CM_10HZ",
            "CM_20HZ",
            "CM_50HZ",
            "CM_100HZ",
            "CM_200HZ",
            "CM_1000HZ",
        )
        return values[self._cmfc]

    @continuous_mode_frequency.setter
    def continuous_mode_frequency(self, value: int) -> None:
        """
        设置连续模式频率。

        Args:
            value (int): 频率常量，必须为continuous_mode_frequency_values中之一

        Raises:
            ValueError: value无效，或频率与带宽不匹配(如200Hz要求带宽≥200Hz，1000Hz要求带宽≥800Hz)

        Notes:
            设置频率前会临时切换为单次模式，设置完成后恢复连续模式。

        ==========================================
        Set continuous mode frequency.

        Args:
            value (int): Frequency constant, must be one of continuous_mode_frequency_values

        Raises:
            ValueError: value is invalid, or frequency does not match bandwidth (200Hz requires bandwidth≥200Hz, 1000Hz requires bandwidth≥800Hz)

        Notes:
            Temporarily switches to single-shot mode before setting frequency, then restores continuous mode.
        """
        if value not in continuous_mode_frequency_values:
            raise ValueError("Value must be a valid continuous_mode_frequency setting")
        if value == CM_200HZ and self._bandwidth < BW_200HZ:
            raise ValueError("Please set a correct bandwidth value for this setting")
        if value == CM_1000HZ and self._bandwidth < BW_800HZ:
            raise ValueError("Please set a correct bandwidth value for this setting")

        self.operation_mode = ONE_SHOT
        self._continuous_mode_frequency = value
        self._cmfc = value
        self.operation_mode = CONTINUOUS

    @property
    def bandwidth(self) -> str:
        """
        获取带宽字符串描述。

        Returns:
            str: 带宽字符串，'BW_100HZ'、'BW_200HZ'、'BW_400HZ'或'BW_800HZ'

        Notes:
            带宽影响测量噪声和转换时间，X/Y/Z通道并行测量。

        ==========================================
        Get bandwidth as string.

        Returns:
            str: Bandwidth string, 'BW_100HZ', 'BW_200HZ', 'BW_400HZ', or 'BW_800HZ'

        Notes:
            Bandwidth affects measurement noise and conversion time. X/Y/Z channels are measured in parallel.
        """
        values = ("BW_100HZ", "BW_200HZ", "BW_400HZ", "BW_800HZ")
        return values[self._bw_cached]

    @bandwidth.setter
    def bandwidth(self, value: int) -> None:
        """
        设置带宽。

        Args:
            value (int): 带宽常量，必须为bandwidth_values中之一

        Raises:
            ValueError: value无效

        Notes:
            设置带宽前会临时切换为单次模式，设置完成后恢复连续模式。

        ==========================================
        Set bandwidth.

        Args:
            value (int): Bandwidth constant, must be one of bandwidth_values

        Raises:
            ValueError: value is invalid

        Notes:
            Temporarily switches to single-shot mode before setting bandwidth, then restores continuous mode.
        """
        if value not in bandwidth_values:
            raise ValueError("Value must be a valid bandwidth setting")
        self.operation_mode = ONE_SHOT
        self._bandwidth = value
        self._bw_cached = value
        self.operation_mode = CONTINUOUS

    @property
    def magnetic(self) -> Tuple[float, float, float]:
        """
        读取磁场强度数据(微特斯拉)。

        Returns:
            Tuple[float, float, float]: 包含X、Y、Z轴磁场强度的三元组，单位μT

        Notes:
            从原始18位数据解包并缩放至±100μT范围。缩放公式基于满量程±131072 LSB对应±100μT。

        ==========================================
        Read magnetic field strength data (microteslas).

        Returns:
            Tuple[float, float, float]: Tuple of X, Y, Z axis magnetic field strength in μT

        Notes:
            Unpacks raw 18-bit data and scales to ±100μT range. Scaling formula based on full scale
            ±131072 LSB corresponding to ±100μT.
        """
        # 读取原始数据(3个16位+1个8位)
        x, y, z, extra = self._raw_data
        time.sleep(0.2)
        # 组合成18位数据
        x_raw = (x << 2) | (((extra & 0xC0) >> 6) & 0x3)
        y_raw = (y << 2) | (((extra & 0x30) >> 4) & 0x3)
        z_raw = (z << 2) | (((extra & 0x03) >> 2) & 0x3)

        # 缩放至±100μT范围
        x_scale = x_raw - 131072.0
        x_scale = (x_scale / 131072.0) * 100

        y_scale = y_raw - 131072.0
        y_scale = (y_scale / 131072.0) * 100

        z_scale = z_raw - 131072.0
        z_scale = (z_scale / 131072.0) * 100

        return x_scale, y_scale, z_scale

    @property
    def temperature(self) -> float:
        """
        读取温度传感器数据(摄氏度)。

        Returns:
            float: 温度值，单位℃

        Notes:
            执行单次温度测量，公式: T = raw * 200/256 - 75。

        ==========================================
        Read temperature sensor data (Celsius).

        Returns:
            float: Temperature value in ℃

        Notes:
            Performs a single temperature measurement. Formula: T = raw * 200/256 - 75.
        """
        # 切换至单次模式进行温度测量
        self.operation_mode = ONE_SHOT
        self._start_temperature_measure = True

        # 读取原始温度值
        t_raw = self._temperature
        # 恢复连续模式
        self.operation_mode = CONTINUOUS

        # 转换为摄氏度
        return t_raw * 200.0 / 256.0 - 75.0


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
