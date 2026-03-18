# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午3:30
# @Author  : jposada202020
# @File    : mma8451.py
# @Description : MMA8451三轴加速度计MicroPython驱动模块。提供加速度读取、量程、数据率等配置。参考自：https://github.com/jposada202020/MicroPython_MMA8451
# @License : MIT
__version__ = "0.1.0"
__author__ = "jposada202020"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

"""
`mma8451` - MMA8451 三轴加速度计 MicroPython 驱动模块
===============================================================================

MicroPython module for the MMA8451 3-axis accelerometer.
MicroPython 模块，用于 MMA8451 三轴加速度计。

* Author(s): Jose D. Montoya
"""

# ======================================== 导入相关模块 =========================================

from micropython import const
from micropython_mma8451.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass

# ======================================== 全局变量 ============================================

# 设备ID寄存器地址
_REG_WHOAMI = const(0x0D)
# 数据输出寄存器起始地址
_DATA = const(0x01)
# XYZ数据配置寄存器
_XYZ_DATA_CFG = const(0x0E)
# 控制寄存器1
_CTRL_REG1 = const(0x2A)
# 高通滤波器截止频率寄存器
_HP_FILTER_CUTOFF = const(0x2F)

# 重力加速度常数 (m/s^2)
_GRAVITY = 9.80665

# 待机模式
STANDBY_MODE = const(0b0)
# 激活模式
ACTIVE_MODE = const(0b1)
# 操作模式可选值元组
operation_mode_values = (STANDBY_MODE, ACTIVE_MODE)

# 量程 ±2g
RANGE_2G = const(0b00)
# 量程 ±4g
RANGE_4G = const(0b01)
# 量程 ±8g
RANGE_8G = const(0b10)
# 量程可选值元组
scale_range_values = (RANGE_2G, RANGE_4G, RANGE_8G)
# 量程与除法因子映射字典
scale_conversion = {RANGE_2G: 4096.0, RANGE_4G: 2048.0, RANGE_8G: 1024.0}

# 数据率 800Hz
DATARATE_800HZ = const(0b000)
# 数据率 400Hz
DATARATE_400HZ = const(0b001)
# 数据率 200Hz
DATARATE_200HZ = const(0b010)
# 数据率 100Hz
DATARATE_100HZ = const(0b011)
# 数据率 50Hz
DATARATE_50HZ = const(0b100)
# 数据率 12.5Hz
DATARATE_12_5HZ = const(0b101)
# 数据率 6.25Hz
DATARATE_6_25HZ = const(0b110)
# 数据率 1.56Hz
DATARATE_1_56HZ = const(0b111)
# 数据率可选值元组
data_rate_values = (
    DATARATE_800HZ,
    DATARATE_400HZ,
    DATARATE_200HZ,
    DATARATE_100HZ,
    DATARATE_50HZ,
    DATARATE_12_5HZ,
    DATARATE_6_25HZ,
    DATARATE_1_56HZ,
)

# 高通滤波器禁用
HPF_DISABLED = const(0b0)
# 高通滤波器启用
HPF_ENABLED = const(0b1)
# 高通滤波器可选值元组
high_pass_filter_values = (HPF_DISABLED, HPF_ENABLED)

# 高通滤波器截止频率 16Hz
CUTOFF_16HZ = const(0b00)
# 高通滤波器截止频率 8Hz
CUTOFF_8HZ = const(0b01)
# 高通滤波器截止频率 4Hz
CUTOFF_4HZ = const(0b10)
# 高通滤波器截止频率 2Hz
CUTOFF_2HZ = const(0b11)
# 高通滤波器截止频率可选值元组
high_pass_filter_cutoff_values = (CUTOFF_16HZ, CUTOFF_8HZ, CUTOFF_4HZ, CUTOFF_2HZ)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MMA8451:
    """
    MMA8451 三轴加速度计驱动器，通过 I2C 接口连接。

    Attributes:
        i2c (machine.I2C): 用于通信的 I2C 总线对象。
        address (int): 设备的 I2C 地址，默认为 0x1D。
        acceleration (Tuple[float, float, float]): 加速度值元组 (x, y, z)，单位 m/s^2。
        operation_mode (str): 当前操作模式字符串，如 "STANDBY_MODE" 或 "ACTIVE_MODE"。
        scale_range (str): 当前量程字符串，如 "RANGE_2G", "RANGE_4G", "RANGE_8G"。
        data_rate (str): 当前数据率字符串，如 "DATARATE_800HZ"。
        high_pass_filter (str): 高通滤波器状态字符串，如 "HPF_DISABLED", "HPF_ENABLED"。
        high_pass_filter_cutoff (str): 高通滤波器截止频率字符串，如 "CUTOFF_16HZ"。

    Methods:
        __init__(i2c, address=0x1D): 初始化传感器实例。

    Notes:
        在更改某些配置（如量程、数据率、滤波器）时，传感器会自动切换到待机模式，设置完成后再返回激活模式。
        如果设备ID不匹配，构造函数会引发 RuntimeError。

    ==========================================
    Driver for the MMA8451 3-axis accelerometer connected via I2C.

    Attributes:
        i2c (machine.I2C): The I2C bus object used for communication.
        address (int): The I2C address of the device, default 0x1D.
        acceleration (Tuple[float, float, float]): Acceleration tuple (x, y, z) in m/s^2.
        operation_mode (str): Current operation mode string, e.g., "STANDBY_MODE" or "ACTIVE_MODE".
        scale_range (str): Current scale range string, e.g., "RANGE_2G", "RANGE_4G", "RANGE_8G".
        data_rate (str): Current data rate string, e.g., "DATARATE_800HZ".
        high_pass_filter (str): High-pass filter status string, e.g., "HPF_DISABLED", "HPF_ENABLED".
        high_pass_filter_cutoff (str): High-pass filter cutoff frequency string, e.g., "CUTOFF_16HZ".

    Methods:
        __init__(i2c, address=0x1D): Initialize the sensor instance.

    Notes:
        When changing certain configurations (scale range, data rate, filters), the sensor automatically
        switches to standby mode, applies the setting, and returns to active mode.
        A RuntimeError is raised if the device ID does not match.
    """

    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _raw_data = RegisterStruct(_DATA, ">hhh")
    _operation_mode = CBits(1, _CTRL_REG1, 0)
    _scale_range = CBits(2, _XYZ_DATA_CFG, 0)
    _data_rate = CBits(2, _CTRL_REG1, 4)

    _high_pass_filter = CBits(1, _XYZ_DATA_CFG, 4)
    _high_pass_filter_cutoff = CBits(2, _HP_FILTER_CUTOFF, 0)

    def __init__(self, i2c, address: int = 0x1D) -> None:
        """

        初始化 MMA8451 传感器。

        Args:
            i2c (machine.I2C): 已配置的 I2C 总线对象。
            address (int): 设备 I2C 地址，默认为 0x1D。

        Raises:
            RuntimeError: 如果未找到传感器（设备ID不匹配）。

        Notes:
            构造函数将传感器置于激活模式。

        ==========================================

        Initialize the MMA8451 sensor.

        Args:
            i2c (machine.I2C): The configured I2C bus object.
            address (int): The I2C device address, default 0x1D.

        Raises:
            RuntimeError: If the sensor is not found (device ID mismatch).

        Notes:
            The constructor sets the sensor to active mode.
        """
        self._i2c = i2c
        self._address = address

        self._operation_mode = ACTIVE_MODE
        self._scale_range_cached = self._scale_range

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """

        获取三轴加速度值。

        Args:
            无

        Returns:
            Tuple[float, float, float]: 包含 x, y, z 轴加速度的元组，单位 m/s^2。

        Notes:
            原始数据右移两位以对齐16位数据，然后根据当前量程转换为物理单位。

        ==========================================

        Get the three-axis acceleration values.

        Args:
            None

        Returns:
            Tuple[float, float, float]: A tuple containing x, y, z acceleration in m/s^2.

        Notes:
            Raw data is shifted right by two bits to align 16-bit data, then converted to physical units
            based on the current scale range.
        """
        x, y, z = self._raw_data
        x >>= 2
        y >>= 2
        z >>= 2

        divisor = scale_conversion[self._scale_range_cached]

        return x / divisor * _GRAVITY, y / divisor * _GRAVITY, z / divisor * _GRAVITY

    @property
    def operation_mode(self) -> str:
        """

        获取当前操作模式。

        Args:
            无

        Returns:
            str: 操作模式字符串，可能为 "STANDBY_MODE" 或 "ACTIVE_MODE"。

        Notes:
            该属性为只读，通过 setter 修改。

        ==========================================

        Get the current operation mode.

        Args:
            None

        Returns:
            str: Operation mode string, either "STANDBY_MODE" or "ACTIVE_MODE".

        Notes:
            This property is read-only; use the setter to modify.
        """
        values = ("STANDBY_MODE", "ACTIVE_MODE")
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        """

        设置操作模式。

        Args:
            value (int): 操作模式常量，应为 STANDBY_MODE 或 ACTIVE_MODE。

        Raises:
            ValueError: 如果 value 不是有效的操作模式。

        Notes:
            设置后立即生效。

        ==========================================

        Set the operation mode.

        Args:
            value (int): Operation mode constant, should be STANDBY_MODE or ACTIVE_MODE.

        Raises:
            ValueError: If value is not a valid operation mode.

        Notes:
            The change takes effect immediately.
        """
        if value not in operation_mode_values:
            raise ValueError("Value must be a valid operation_mode setting")
        self._operation_mode = value

    @property
    def scale_range(self) -> str:
        """

        获取当前量程。

        Args:
            无

        Returns:
            str: 量程字符串，可能为 "RANGE_2G", "RANGE_4G", "RANGE_8G"。

        Notes:
            该属性为只读，通过 setter 修改。

        ==========================================

        Get the current scale range.

        Args:
            None

        Returns:
            str: Scale range string, either "RANGE_2G", "RANGE_4G", or "RANGE_8G".

        Notes:
            This property is read-only; use the setter to modify.
        """
        values = ("RANGE_2G", "RANGE_4G", "RANGE_8G")
        return values[self._scale_range]

    @scale_range.setter
    def scale_range(self, value: int) -> None:
        """

        设置量程。

        Args:
            value (int): 量程常量，应为 RANGE_2G, RANGE_4G 或 RANGE_8G。

        Raises:
            ValueError: 如果 value 不是有效的量程。

        Notes:
            更改量程时，传感器会暂时切换到待机模式，设置完成后再返回激活模式。

        ==========================================

        Set the scale range.

        Args:
            value (int): Scale range constant, should be RANGE_2G, RANGE_4G, or RANGE_8G.

        Raises:
            ValueError: If value is not a valid scale range.

        Notes:
            When changing the scale range, the sensor temporarily switches to standby mode,
            applies the setting, and then returns to active mode.
        """
        if value not in scale_range_values:
            raise ValueError("Value must be a valid scale_range setting")
        self._operation_mode = STANDBY_MODE
        self._scale_range = value
        self._scale_range_cached = value
        self._operation_mode = ACTIVE_MODE

    @property
    def data_rate(self) -> str:
        """

        获取当前数据率。

        Args:
            无

        Returns:
            str: 数据率字符串，如 "DATARATE_800HZ", "DATARATE_400HZ" 等。

        Notes:
            该属性为只读，通过 setter 修改。

        ==========================================

        Get the current data rate.

        Args:
            None

        Returns:
            str: Data rate string, e.g., "DATARATE_800HZ", "DATARATE_400HZ", etc.

        Notes:
            This property is read-only; use the setter to modify.
        """
        values = (
            "DATARATE_800HZ",
            "DATARATE_400HZ",
            "DATARATE_200HZ",
            "DATARATE_100HZ",
            "DATARATE_50HZ",
            "DATARATE_12_5HZ",
            "DATARATE_6_25HZ",
            "DATARATE_1_56HZ",
        )
        return values[self._data_rate]

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        """

        设置数据率。

        Args:
            value (int): 数据率常量，应为 data_rate_values 中的值。

        Raises:
            ValueError: 如果 value 不是有效的数据率。

        Notes:
            更改数据率时，传感器会暂时切换到待机模式，设置完成后再返回激活模式。

        ==========================================

        Set the data rate.

        Args:
            value (int): Data rate constant, should be one of data_rate_values.

        Raises:
            ValueError: If value is not a valid data rate.

        Notes:
            When changing the data rate, the sensor temporarily switches to standby mode,
            applies the setting, and then returns to active mode.
        """
        if value not in data_rate_values:
            raise ValueError("Value must be a valid data_rate setting")
        self._operation_mode = STANDBY_MODE
        self._data_rate = value
        self._operation_mode = ACTIVE_MODE

    @property
    def high_pass_filter(self) -> str:
        """

        获取高通滤波器状态。

        Args:
            无

        Returns:
            str: 滤波器状态字符串，可能为 "HPF_DISABLED" 或 "HPF_ENABLED"。

        Notes:
            该属性为只读，通过 setter 修改。

        ==========================================

        Get the high-pass filter status.

        Args:
            None

        Returns:
            str: Filter status string, either "HPF_DISABLED" or "HPF_ENABLED".

        Notes:
            This property is read-only; use the setter to modify.
        """
        values = ("HPF_DISABLED", "HPF_ENABLED")
        return values[self._high_pass_filter]

    @high_pass_filter.setter
    def high_pass_filter(self, value: int) -> None:
        """

        设置高通滤波器状态。

        Args:
            value (int): 滤波器常量，应为 HPF_DISABLED 或 HPF_ENABLED。

        Raises:
            ValueError: 如果 value 不是有效的滤波器状态。

        Notes:
            更改滤波器状态时，传感器会暂时切换到待机模式，设置完成后再返回激活模式。

        ==========================================

        Set the high-pass filter status.

        Args:
            value (int): Filter constant, should be HPF_DISABLED or HPF_ENABLED.

        Raises:
            ValueError: If value is not a valid filter status.

        Notes:
            When changing the filter status, the sensor temporarily switches to standby mode,
            applies the setting, and then returns to active mode.
        """
        if value not in high_pass_filter_values:
            raise ValueError("Value must be a valid high_pass_filter setting")
        self._operation_mode = STANDBY_MODE
        self._high_pass_filter = value
        self._operation_mode = ACTIVE_MODE

    @property
    def high_pass_filter_cutoff(self) -> str:
        """

        获取高通滤波器截止频率。

        Args:
            无

        Returns:
            str: 截止频率字符串，可能为 "CUTOFF_16HZ", "CUTOFF_8HZ", "CUTOFF_4HZ", "CUTOFF_2HZ"。

        Notes:
            该属性为只读，通过 setter 修改。要使设置生效，必须启用高通滤波器。

        ==========================================

        Get the high-pass filter cutoff frequency.

        Args:
            None

        Returns:
            str: Cutoff frequency string, either "CUTOFF_16HZ", "CUTOFF_8HZ", "CUTOFF_4HZ", or "CUTOFF_2HZ".

        Notes:
            This property is read-only; use the setter to modify. The high-pass filter must be enabled
            for this setting to take effect.
        """
        values = ("CUTOFF_16HZ", "CUTOFF_8HZ", "CUTOFF_4HZ", "CUTOFF_2HZ")
        return values[self._high_pass_filter_cutoff]

    @high_pass_filter_cutoff.setter
    def high_pass_filter_cutoff(self, value: int) -> None:
        """

        设置高通滤波器截止频率。

        Args:
            value (int): 截止频率常量，应为 high_pass_filter_cutoff_values 中的值。

        Raises:
            ValueError: 如果 value 不是有效的截止频率。

        Notes:
            更改截止频率时，传感器会暂时切换到待机模式，设置完成后再返回激活模式。

        ==========================================

        Set the high-pass filter cutoff frequency.

        Args:
            value (int): Cutoff frequency constant, should be one of high_pass_filter_cutoff_values.

        Raises:
            ValueError: If value is not a valid cutoff frequency.

        Notes:
            When changing the cutoff frequency, the sensor temporarily switches to standby mode,
            applies the setting, and then returns to active mode.
        """
        if value not in high_pass_filter_cutoff_values:
            raise ValueError("Value must be a valid high_pass_filter_cutoff setting")
        self._operation_mode = STANDBY_MODE
        self._high_pass_filter_cutoff = value
        self._operation_mode = ACTIVE_MODE


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
