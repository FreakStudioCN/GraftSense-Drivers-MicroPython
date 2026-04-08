# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/27 下午5:00
# @Author  : Jose D. Montoya
# @File    : h3lis200dl.py
# @Description : ST H3LIS200DL三轴加速度计MicroPython驱动
# @License : MIT
# __version__ = "0.1.0"
# __author__ = "Jose D. Montoya"
# __license__ = "MIT"
# __platform__ = "MicroPython v1.23.0"

# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`h3lis200dl`
================================================================================

Micropython Driver for the ST H3LIS200DL Accelerometer


* Author(s): Jose D. Montoya


"""

# ======================================== 导入相关模块 =========================================

from collections import namedtuple
from micropython import const
from micropython_h3lis200dl.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_H3LIS200DL.git"

# ======================================== 全局变量 ============================================

# 寄存器地址定义
_REG_WHOAMI = const(0x0F)  # WHO_AM_I寄存器地址
_CTRL_REG1 = const(0x20)  # 控制寄存器1地址
_CTRL_REG2 = const(0x21)  # 控制寄存器2地址
_CTRL_REG3 = const(0x22)  # 控制寄存器3地址
_CTRL_REG4 = const(0x23)  # 控制寄存器4地址
_INT1_CFG = const(0x30)  # 中断1配置寄存器地址
_INT1_SRC = const(0x31)  # 中断1源寄存器地址
_INT1_THS = const(0x32)  # 中断1阈值寄存器地址
_INT1_DURATION = const(0x33)  # 中断1持续时间寄存器地址
_INT2_CFG = const(0x34)  # 中断2配置寄存器地址
_INT2_SRC = const(0x35)  # 中断2源寄存器地址
_INT2_THS = const(0x36)  # 中断2阈值寄存器地址
_INT2_DURATION = const(0x37)  # 中断2持续时间寄存器地址

# 加速度数据寄存器地址
_ACC_X = const(0x29)  # X轴加速度数据寄存器
_ACC_Y = const(0x2B)  # Y轴加速度数据寄存器
_ACC_Z = const(0x2D)  # Z轴加速度数据寄存器

# 重力加速度转换常数
_G_TO_ACCEL = 9.80665  # g值到m/s²的转换因子

# 工作模式定义
POWER_DOWN = const(0b000)  # 掉电模式
NORMAL_MODE = const(0b001)  # 正常模式
LOW_POWER_ODR0_5 = const(0b010)  # 低功耗模式，ODR=0.5Hz
LOW_POWER_ODR1 = const(0b011)  # 低功耗模式，ODR=1Hz
LOW_POWER_ODR2 = const(0b100)  # 低功耗模式，ODR=2Hz
LOW_POWER_ODR5 = const(0b101)  # 低功耗模式，ODR=5Hz
LOW_POWER_ODR10 = const(0b110)  # 低功耗模式，ODR=10Hz
# 有效的工作模式值列表
operation_mode_values = (
    POWER_DOWN,
    NORMAL_MODE,
    LOW_POWER_ODR0_5,
    LOW_POWER_ODR1,
    LOW_POWER_ODR2,
    LOW_POWER_ODR5,
    LOW_POWER_ODR10,
)

# 数据速率定义
RATE_50HZ = const(0b00)  # 50Hz
RATE_100HZ = const(0b01)  # 100Hz
RATE_400HZ = const(0b10)  # 400Hz
RATE_1000HZ = const(0b11)  # 1000Hz
# 有效的数据速率值列表
data_rate_values = (RATE_50HZ, RATE_100HZ, RATE_400HZ, RATE_1000HZ)

# 轴启用状态定义
X_DISABLED = const(0b0)  # X轴禁用
X_ENABLED = const(0b1)  # X轴启用
Y_DISABLED = const(0b0)  # Y轴禁用
Y_ENABLED = const(0b1)  # Y轴启用
Z_DISABLED = const(0b0)  # Z轴禁用
Z_ENABLED = const(0b1)  # Z轴启用
# 轴启用状态有效值列表
axis_enabled_values = (X_DISABLED, X_ENABLED)

# 满量程选择定义
SCALE_100G = const(0b0)  # ±100g量程
SCALE_200G = const(0b1)  # ±200g量程
# 有效满量程值列表
full_scale_selection_values = (SCALE_100G, SCALE_200G)
# 满量程到实际值的映射
full_scale = {SCALE_100G: 100, SCALE_200G: 200}

# 高通滤波器模式定义
FILTER_NORMAL_MODE = const(0b00)  # 正常模式
FILTER_SIGNAL_FILTERING = const(0b01)  # 信号滤波模式
# 有效高通滤波器模式值列表
high_pass_filter_mode_values = (FILTER_NORMAL_MODE, FILTER_SIGNAL_FILTERING)

# 高通滤波器截止频率选择定义
HPCF8 = const(0b00)  # 截止频率系数8
HPCF16 = const(0b01)  # 截止频率系数16
HPCF32 = const(0b10)  # 截止频率系数32
HPCF64 = const(0b11)  # 截止频率系数64
# 有效高通滤波器截止频率值列表
high_pass_filter_cutoff_values = (HPCF8, HPCF16, HPCF32, HPCF64)

# 告警状态命名元组
AlertStatus = namedtuple("AlertStatus", ["high_g", "low_g"])

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# pylint: disable=too-many-instance-attributes
class H3LIS200DL:
    """
    H3LIS200DL传感器I2C驱动类，提供加速度数据读取和配置功能。

    Attributes:
        _i2c (I2C): I2C总线对象
        _address (int): 设备I2C地址
        _memory_full_scale_selection (int): 缓存的满量程选择值

    Methods:
        acceleration(): 读取三轴加速度数据
        operation_mode(): 设置/获取工作模式
        full_scale_selection(): 设置/获取满量程
        x_enabled(): 设置/获取X轴使能状态
        y_enabled(): 设置/获取Y轴使能状态
        z_enabled(): 设置/获取Z轴使能状态
        data_rate(): 设置/获取数据速率
        high_pass_filter_mode(): 设置/获取高通滤波器模式
        high_pass_filter_cutoff(): 设置/获取高通滤波器截止频率
        interrupt1_configuration(): 设置/获取中断1配置
        interrupt1_threshold(): 设置/获取中断1阈值
        interrupt1_duration(): 设置/获取中断1持续时间
        interrupt1_source_register(): 读取中断1源寄存器
        interrupt1_latched(): 设置/获取中断1锁存模式
        interrupt2_configuration(): 设置/获取中断2配置
        interrupt2_threshold(): 设置/获取中断2阈值
        interrupt2_duration(): 设置/获取中断2持续时间
        interrupt2_source_register(): 读取中断2源寄存器
        interrupt2_latched(): 设置/获取中断2锁存模式

    Notes:
        本驱动支持±100g/±200g量程，数据速率最高1kHz，提供低功耗模式。

    ==========================================
    I2C driver for H3LIS200DL sensor, provides acceleration data reading and configuration.

    Attributes:
        _i2c (I2C): I2C bus object
        _address (int): Device I2C address
        _memory_full_scale_selection (int): Cached full scale selection value

    Methods:
        acceleration(): Read three-axis acceleration data
        operation_mode(): Set/get operation mode
        full_scale_selection(): Set/get full scale
        x_enabled(): Set/get X-axis enable state
        y_enabled(): Set/get Y-axis enable state
        z_enabled(): Set/get Z-axis enable state
        data_rate(): Set/get data rate
        high_pass_filter_mode(): Set/get high-pass filter mode
        high_pass_filter_cutoff(): Set/get high-pass filter cutoff
        interrupt1_configuration(): Set/get interrupt1 configuration
        interrupt1_threshold(): Set/get interrupt1 threshold
        interrupt1_duration(): Set/get interrupt1 duration
        interrupt1_source_register(): Read interrupt1 source register
        interrupt1_latched(): Set/get interrupt1 latch mode
        interrupt2_configuration(): Set/get interrupt2 configuration
        interrupt2_threshold(): Set/get interrupt2 threshold
        interrupt2_duration(): Set/get interrupt2 duration
        interrupt2_source_register(): Read interrupt2 source register
        interrupt2_latched(): Set/get interrupt2 latch mode

    Notes:
        This driver supports ±100g/±200g ranges, data rates up to 1kHz, and low power modes.
    """

    # 寄存器结构体定义
    _device_id = RegisterStruct(_REG_WHOAMI, "B")  # 设备ID寄存器
    _int1_configuration = RegisterStruct(_INT1_CFG, "B")  # 中断1配置寄存器
    _int1_source_register = RegisterStruct(_INT1_SRC, "B")  # 中断1源寄存器
    _int1_threshold = RegisterStruct(_INT1_THS, "B")  # 中断1阈值寄存器
    _int1_duration = RegisterStruct(_INT1_DURATION, "B")  # 中断1持续时间寄存器
    _int1_latched = CBits(1, _CTRL_REG3, 2)  # 中断1锁存位

    _int2_configuration = RegisterStruct(_INT2_CFG, "B")  # 中断2配置寄存器
    _int2_source_register = RegisterStruct(_INT2_SRC, "B")  # 中断2源寄存器
    _int2_threshold = RegisterStruct(_INT2_THS, "B")  # 中断2阈值寄存器
    _int2_duration = RegisterStruct(_INT2_DURATION, "B")  # 中断2持续时间寄存器
    _int2_latched = CBits(1, _CTRL_REG3, 5)  # 中断2锁存位

    # 加速度数据寄存器
    _acc_data_x = RegisterStruct(_ACC_X, "B")  # X轴加速度数据
    _acc_data_y = RegisterStruct(_ACC_Y, "B")  # Y轴加速度数据
    _acc_data_z = RegisterStruct(_ACC_Z, "B")  # Z轴加速度数据

    _full_scale_selection = CBits(1, _CTRL_REG4, 4)  # 满量程选择位

    # 控制寄存器1 (0x20) 位定义
    _operation_mode = CBits(3, _CTRL_REG1, 5)  # 工作模式位
    _data_rate = CBits(2, _CTRL_REG1, 3)  # 数据速率位
    _z_enabled = CBits(1, _CTRL_REG1, 2)  # Z轴使能位
    _y_enabled = CBits(1, _CTRL_REG1, 1)  # Y轴使能位
    _x_enabled = CBits(1, _CTRL_REG1, 0)  # X轴使能位

    # 控制寄存器2 (0x21) 位定义
    _high_pass_filter_mode = CBits(2, _CTRL_REG2, 5)  # 高通滤波器模式位
    _high_pass_filter_cutoff = CBits(2, _CTRL_REG2, 0)  # 高通滤波器截止频率位

    def __init__(self, i2c, address: int = 0x19) -> None:
        """
        初始化H3LIS200DL传感器

        Args:
            i2c (I2C): I2C总线对象
            address (int): I2C设备地址，默认为0x19

        Raises:
            RuntimeError: 如果未找到传感器（设备ID不匹配）

        Notes:
            初始化后默认设置为正常模式，所有轴使能，满量程为±200g。

        ==========================================
        Initialize H3LIS200DL sensor

        Args:
            i2c (I2C): I2C bus object
            address (int): I2C device address, default 0x19

        Raises:
            RuntimeError: If sensor is not found (device ID mismatch)

        Notes:
            After initialization, default settings are normal mode, all axes enabled, full scale ±200g.
        """
        self._i2c = i2c
        self._address = address

        # 检查设备ID，应为0x32
        if self._device_id != 0x32:
            raise RuntimeError("Failed to find the H3LIS200DL sensor")

        self._operation_mode = NORMAL_MODE
        self._memory_full_scale_selection = self._full_scale_selection

    @property
    def operation_mode(self) -> str:
        """
        获取当前工作模式名称

        Returns:
            str: 工作模式字符串，如"NORMAL_MODE"

        Notes:
            工作模式决定了功耗和数据输出速率，详见数据手册。

        ==========================================
        Get current operation mode name

        Returns:
            str: Operation mode string, e.g. "NORMAL_MODE"

        Notes:
            Operation mode determines power consumption and data output rate, see datasheet.
        """
        values = (
            "POWER_DOWN",
            "NORMAL_MODE",
            "LOW_POWER_ODR0_5",
            "LOW_POWER_ODR1",
            "LOW_POWER_ODR2",
            "LOW_POWER_ODR5",
            "LOW_POWER_ODR10",
        )
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        """
        设置工作模式

        Args:
            value (int): 工作模式值，必须为预定义常量之一

        Raises:
            ValueError: 如果值无效

        Notes:
            有效值包括：POWER_DOWN, NORMAL_MODE, LOW_POWER_ODR0_5等。

        ==========================================
        Set operation mode

        Args:
            value (int): Operation mode value, must be one of predefined constants

        Raises:
            ValueError: If value is invalid

        Notes:
            Valid values include: POWER_DOWN, NORMAL_MODE, LOW_POWER_ODR0_5, etc.
        """
        if value not in operation_mode_values:
            raise ValueError("Value must be a valid operation_mode setting")
        self._operation_mode = value

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """
        读取三轴加速度数据

        Returns:
            Tuple[float, float, float]: (x, y, z) 加速度值，单位g

        Notes:
            数据基于当前满量程设置进行换算，原始数据为8位有符号数。

        ==========================================
        Read three-axis acceleration data

        Returns:
            Tuple[float, float, float]: (x, y, z) acceleration values in g

        Notes:
            Data is scaled according to current full scale setting, raw data is 8-bit signed.
        """
        x = self._twos_comp(self._acc_data_x, 8) * full_scale[self._memory_full_scale_selection] / 128
        y = self._twos_comp(self._acc_data_y, 8) * full_scale[self._memory_full_scale_selection] / 128
        z = self._twos_comp(self._acc_data_z, 8) * full_scale[self._memory_full_scale_selection] / 128
        return x, y, z

    @property
    def full_scale_selection(self) -> str:
        """
        获取当前满量程设置

        Returns:
            str: 满量程字符串，如"SCALE_100G"或"SCALE_200G"

        ==========================================
        Get current full scale setting

        Returns:
            str: Full scale string, e.g. "SCALE_100G" or "SCALE_200G"
        """
        values = (
            "SCALE_100G",
            "SCALE_200G",
        )
        return values[self._full_scale_selection]

    @full_scale_selection.setter
    def full_scale_selection(self, value: int) -> None:
        """
        设置满量程

        Args:
            value (int): 满量程值，SCALE_100G或SCALE_200G

        Raises:
            ValueError: 如果值无效

        Notes:
            满量程影响加速度测量范围，±100g或±200g。

        ==========================================
        Set full scale

        Args:
            value (int): Full scale value, SCALE_100G or SCALE_200G

        Raises:
            ValueError: If value is invalid

        Notes:
            Full scale affects acceleration measurement range, ±100g or ±200g.
        """
        if value not in full_scale_selection_values:
            raise ValueError("Value must be a valid full_scale_selection setting")
        self._full_scale_selection = value
        self._memory_full_scale_selection = value

    @staticmethod
    def _twos_comp(val: int, bits: int) -> int:
        """
        将无符号整数转换为有符号补码值

        Args:
            val (int): 原始无符号值
            bits (int): 位数

        Returns:
            int: 有符号值

        ==========================================
        Convert unsigned integer to signed two's complement

        Args:
            val (int): Raw unsigned value
            bits (int): Number of bits

        Returns:
            int: Signed value
        """
        if val & (1 << (bits - 1)) != 0:
            return val - (1 << bits)
        return val

    @property
    def x_enabled(self) -> str:
        """
        获取X轴使能状态

        Returns:
            str: "X_ENABLED"或"X_DISABLED"

        ==========================================
        Get X-axis enable state

        Returns:
            str: "X_ENABLED" or "X_DISABLED"
        """
        values = (
            "X_DISABLED",
            "X_ENABLED",
        )
        return values[self._x_enabled]

    @x_enabled.setter
    def x_enabled(self, value: int) -> None:
        """
        设置X轴使能状态

        Args:
            value (int): X_ENABLED或X_DISABLED

        Raises:
            ValueError: 如果值无效

        Notes:
            禁用未使用的轴可以降低功耗。

        ==========================================
        Set X-axis enable state

        Args:
            value (int): X_ENABLED or X_DISABLED

        Raises:
            ValueError: If value is invalid

        Notes:
            Disabling unused axes reduces power consumption.
        """
        if value not in axis_enabled_values:
            raise ValueError("Value must be a valid x_enabled setting")
        self._x_enabled = value

    @property
    def y_enabled(self) -> str:
        """
        获取Y轴使能状态

        Returns:
            str: "Y_ENABLED"或"Y_DISABLED"

        ==========================================
        Get Y-axis enable state

        Returns:
            str: "Y_ENABLED" or "Y_DISABLED"
        """
        values = (
            "Y_DISABLED",
            "Y_ENABLED",
        )
        return values[self._y_enabled]

    @y_enabled.setter
    def y_enabled(self, value: int) -> None:
        """
        设置Y轴使能状态

        Args:
            value (int): Y_ENABLED或Y_DISABLED

        Raises:
            ValueError: 如果值无效

        ==========================================
        Set Y-axis enable state

        Args:
            value (int): Y_ENABLED or Y_DISABLED

        Raises:
            ValueError: If value is invalid
        """
        if value not in axis_enabled_values:
            raise ValueError("Value must be a valid y_enabled setting")
        self._y_enabled = value

    @property
    def z_enabled(self) -> str:
        """
        获取Z轴使能状态

        Returns:
            str: "Z_ENABLED"或"Z_DISABLED"

        ==========================================
        Get Z-axis enable state

        Returns:
            str: "Z_ENABLED" or "Z_DISABLED"
        """
        values = (
            "Z_DISABLED",
            "Z_ENABLED",
        )
        return values[self._z_enabled]

    @z_enabled.setter
    def z_enabled(self, value: int) -> None:
        """
        设置Z轴使能状态

        Args:
            value (int): Z_ENABLED或Z_DISABLED

        Raises:
            ValueError: 如果值无效

        ==========================================
        Set Z-axis enable state

        Args:
            value (int): Z_ENABLED or Z_DISABLED

        Raises:
            ValueError: If value is invalid
        """
        if value not in axis_enabled_values:
            raise ValueError("Value must be a valid z_enabled setting")
        self._z_enabled = value

    @property
    def data_rate(self) -> str:
        """
        获取数据速率

        Returns:
            str: 数据速率字符串，如"RATE_50HZ"

        ==========================================
        Get data rate

        Returns:
            str: Data rate string, e.g. "RATE_50HZ"
        """
        values = ("RATE_50HZ", "RATE_100HZ", "RATE_400HZ", "RATE_1000HZ")
        return values[self._data_rate]

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        """
        设置数据速率

        Args:
            value (int): 数据速率值，RATE_50HZ等

        Raises:
            ValueError: 如果值无效

        ==========================================
        Set data rate

        Args:
            value (int): Data rate value, RATE_50HZ etc.

        Raises:
            ValueError: If value is invalid
        """
        if value not in data_rate_values:
            raise ValueError("Value must be a valid data_rate setting")
        self._data_rate = value

    @property
    def high_pass_filter_mode(self) -> str:
        """
        获取高通滤波器模式

        Returns:
            str: 滤波器模式字符串，如"FILTER_NORMAL_MODE"

        ==========================================
        Get high-pass filter mode

        Returns:
            str: Filter mode string, e.g. "FILTER_NORMAL_MODE"
        """
        values = ("FILTER_NORMAL_MODE", "FILTER_SIGNAL_FILTERING")
        return values[self._high_pass_filter_mode]

    @high_pass_filter_mode.setter
    def high_pass_filter_mode(self, value: int) -> None:
        """
        设置高通滤波器模式

        Args:
            value (int): 滤波器模式值，FILTER_NORMAL_MODE或FILTER_SIGNAL_FILTERING

        Raises:
            ValueError: 如果值无效

        ==========================================
        Set high-pass filter mode

        Args:
            value (int): Filter mode value, FILTER_NORMAL_MODE or FILTER_SIGNAL_FILTERING

        Raises:
            ValueError: If value is invalid
        """
        if value not in high_pass_filter_mode_values:
            raise ValueError("Value must be a valid high_pass_filter_mode setting")
        self._high_pass_filter_mode = value

    # pylint: disable=line-too-long
    @property
    def high_pass_filter_cutoff(self) -> str:
        """
        获取高通滤波器截止频率系数

        Returns:
            str: 截止频率系数字符串，如"HPCF8"

        Notes:
            实际截止频率取决于数据速率，详见数据手册。

        ==========================================
        Get high-pass filter cutoff coefficient

        Returns:
            str: Cutoff coefficient string, e.g. "HPCF8"

        Notes:
            Actual cutoff frequency depends on data rate, see datasheet.
        """
        values = ("HPCF8", "HPCF16", "HPCF32", "HPCF64")
        return values[self._high_pass_filter_cutoff]

    # pylint: enable=line-too-long
    @high_pass_filter_cutoff.setter
    def high_pass_filter_cutoff(self, value: int) -> None:
        """
        设置高通滤波器截止频率系数

        Args:
            value (int): 截止频率系数值，HPCF8等

        Raises:
            ValueError: 如果值无效

        ==========================================
        Set high-pass filter cutoff coefficient

        Args:
            value (int): Cutoff coefficient value, HPCF8 etc.

        Raises:
            ValueError: If value is invalid
        """
        if value not in high_pass_filter_cutoff_values:
            raise ValueError("Value must be a valid high_pass_filter_cutoff setting")
        self._high_pass_filter_cutoff = value

    @property
    def interrupt1_configuration(self) -> int:
        """
        获取中断1配置寄存器值

        Returns:
            int: 配置寄存器字节

        ==========================================
        Get interrupt1 configuration register value

        Returns:
            int: Configuration register byte
        """
        return self._int1_configuration

    @interrupt1_configuration.setter
    def interrupt1_configuration(self, value: int) -> None:
        """
        设置中断1配置寄存器

        Args:
            value (int): 配置字节，0-255

        Raises:
            ValueError: 如果值超出范围

        ==========================================
        Set interrupt1 configuration register

        Args:
            value (int): Configuration byte, 0-255

        Raises:
            ValueError: If value out of range
        """
        if value > 255:
            raise ValueError("value must be a valid setting")
        self._int1_configuration = value

    @property
    def interrupt1_threshold(self) -> int:
        """
        获取中断1阈值寄存器值

        Returns:
            int: 阈值字节

        ==========================================
        Get interrupt1 threshold register value

        Returns:
            int: Threshold byte
        """
        return self._int1_threshold

    @interrupt1_threshold.setter
    def interrupt1_threshold(self, value: int) -> None:
        """
        设置中断1阈值

        Args:
            value (int): 阈值，0-128

        Raises:
            ValueError: 如果值超出范围

        ==========================================
        Set interrupt1 threshold

        Args:
            value (int): Threshold, 0-128

        Raises:
            ValueError: If value out of range
        """
        if value > 128:
            raise ValueError("value must be a valid setting")
        self._int1_threshold = value

    @property
    def interrupt1_duration(self) -> int:
        """
        获取中断1持续时间寄存器值

        Returns:
            int: 持续时间字节

        ==========================================
        Get interrupt1 duration register value

        Returns:
            int: Duration byte
        """
        return self._int1_duration

    @interrupt1_duration.setter
    def interrupt1_duration(self, value: int) -> None:
        """
        设置中断1持续时间

        Args:
            value (int): 持续时间，0-128

        Raises:
            ValueError: 如果值超出范围

        Notes:
            实际持续时间取决于数据速率，详见数据手册。

        ==========================================
        Set interrupt1 duration

        Args:
            value (int): Duration, 0-128

        Raises:
            ValueError: If value out of range

        Notes:
            Actual duration depends on data rate, see datasheet.
        """
        if value > 128:
            raise ValueError("value must be a valid setting")
        self._int1_duration = value

    @property
    def interrupt1_source_register(self) -> Tuple:
        """
        读取中断1源寄存器，获取各轴中断状态

        Returns:
            Tuple[AlertStatus, AlertStatus, AlertStatus]: (X轴状态, Y轴状态, Z轴状态)
                每个状态包含high_g和low_g布尔值

        ==========================================
        Read interrupt1 source register, get interrupt status for each axis

        Returns:
            Tuple[AlertStatus, AlertStatus, AlertStatus]: (X axis status, Y axis status, Z axis status)
                Each status contains high_g and low_g boolean values
        """
        dummy = self._int1_source_register

        highx = dummy & 0x03 == 2
        highy = (dummy & 0xC) >> 2 == 2
        highz = (dummy & 0x30) >> 4 == 2

        return (
            AlertStatus(high_g=highx, low_g=not highx),
            AlertStatus(high_g=highy, low_g=not highy),
            AlertStatus(high_g=highz, low_g=not highz),
        )

    @property
    def interrupt1_latched(self) -> int:
        """
        获取中断1锁存模式状态

        Returns:
            int: 0（未锁存）或1（锁存）

        ==========================================
        Get interrupt1 latch mode state

        Returns:
            int: 0 (not latched) or 1 (latched)
        """
        return self._int1_latched

    @interrupt1_latched.setter
    def interrupt1_latched(self, value: int) -> None:
        """
        设置中断1锁存模式

        Args:
            value (int): 0（未锁存）或1（锁存）

        Notes:
            锁存模式下，中断状态会保持直到读取INT1_SRC寄存器。

        ==========================================
        Set interrupt1 latch mode

        Args:
            value (int): 0 (not latched) or 1 (latched)

        Notes:
            In latched mode, interrupt status is held until INT1_SRC register is read.
        """
        self._int1_latched = value

    @property
    def interrupt2_configuration(self) -> int:
        """
        获取中断2配置寄存器值

        Returns:
            int: 配置寄存器字节

        ==========================================
        Get interrupt2 configuration register value

        Returns:
            int: Configuration register byte
        """
        return self._int2_configuration

    @interrupt2_configuration.setter
    def interrupt2_configuration(self, value: int) -> None:
        """
        设置中断2配置寄存器

        Args:
            value (int): 配置字节，0-255

        Raises:
            ValueError: 如果值超出范围

        ==========================================
        Set interrupt2 configuration register

        Args:
            value (int): Configuration byte, 0-255

        Raises:
            ValueError: If value out of range
        """
        if value > 255:
            raise ValueError("value must be a valid setting")
        self._int2_configuration = value

    @property
    def interrupt2_threshold(self) -> int:
        """
        获取中断2阈值寄存器值

        Returns:
            int: 阈值字节

        ==========================================
        Get interrupt2 threshold register value

        Returns:
            int: Threshold byte
        """
        return self._int2_threshold

    @interrupt2_threshold.setter
    def interrupt2_threshold(self, value: int) -> None:
        """
        设置中断2阈值

        Args:
            value (int): 阈值，0-128

        Raises:
            ValueError: 如果值超出范围

        ==========================================
        Set interrupt2 threshold

        Args:
            value (int): Threshold, 0-128

        Raises:
            ValueError: If value out of range
        """
        if value > 128:
            raise ValueError("value must be a valid setting")
        self._int2_threshold = value

    @property
    def interrupt2_duration(self) -> int:
        """
        获取中断2持续时间寄存器值

        Returns:
            int: 持续时间字节

        ==========================================
        Get interrupt2 duration register value

        Returns:
            int: Duration byte
        """
        return self._int2_duration

    @interrupt2_duration.setter
    def interrupt2_duration(self, value: int) -> None:
        """
        设置中断2持续时间

        Args:
            value (int): 持续时间，0-128

        Raises:
            ValueError: 如果值超出范围

        ==========================================
        Set interrupt2 duration

        Args:
            value (int): Duration, 0-128

        Raises:
            ValueError: If value out of range
        """
        if value > 128:
            raise ValueError("value must be a valid setting")
        self._int2_duration = value

    @property
    def interrupt2_source_register(self) -> Tuple:
        """
        读取中断2源寄存器，获取各轴中断状态

        Returns:
            Tuple[AlertStatus, AlertStatus, AlertStatus]: (X轴状态, Y轴状态, Z轴状态)
                每个状态包含high_g和low_g布尔值

        ==========================================
        Read interrupt2 source register, get interrupt status for each axis

        Returns:
            Tuple[AlertStatus, AlertStatus, AlertStatus]: (X axis status, Y axis status, Z axis status)
                Each status contains high_g and low_g boolean values
        """
        dummy = self._int2_source_register

        highx = dummy & 0x03 == 2
        highy = (dummy & 0xC) >> 2 == 2
        highz = (dummy & 0x30) >> 4 == 2

        return (
            AlertStatus(high_g=highx, low_g=not highx),
            AlertStatus(high_g=highy, low_g=not highy),
            AlertStatus(high_g=highz, low_g=not highz),
        )

    @property
    def interrupt2_latched(self) -> int:
        """
        获取中断2锁存模式状态

        Returns:
            int: 0（未锁存）或1（锁存）

        ==========================================
        Get interrupt2 latch mode state

        Returns:
            int: 0 (not latched) or 1 (latched)
        """
        return self._int2_latched

    @interrupt2_latched.setter
    def interrupt2_latched(self, value: int) -> None:
        """
        设置中断2锁存模式

        Args:
            value (int): 0（未锁存）或1（锁存）

        ==========================================
        Set interrupt2 latch mode

        Args:
            value (int): 0 (not latched) or 1 (latched)
        """
        self._int2_latched = value


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
