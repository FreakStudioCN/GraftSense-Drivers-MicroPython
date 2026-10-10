# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/18 下午2:15
# @Author  : Jose D. Montoya
# @File    : lis3mdl.py
# @Description : MicroPython驱动用于ST LIS3MDL磁力计
# @License : MIT
__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

import time
from micropython import const
from micropython_lis3mdl.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass


# ======================================== 全局变量 ============================================

# 寄存器地址常量
_REG_WHO_AM_I = const(0x0F)  # 器件标识寄存器，取值0x0F
_CTRL_REG1 = const(0x20)  # 控制寄存器1，地址0x20
_CTRL_REG2 = const(0x21)  # 控制寄存器2，地址0x21
_CTRL_REG3 = const(0x22)  # 控制寄存器3，地址0x22
_CTRL_REG4 = const(0x23)  # 控制寄存器4，地址0x23
_DATA = const(0x28)  # 磁力数据输出寄存器起始地址，地址0x28

# 高斯到微特斯拉转换因子
_GAUSS_TO_UT = 100

# 温度传感器使能模式常量
TEMPERATURE_DISABLED = const(0b0)  # 禁用温度传感器，取值0
TEMPERATURE_ENABLED = const(0b1)  # 启用温度传感器，取值1
temperature_mode_values = (TEMPERATURE_DISABLED, TEMPERATURE_ENABLED)

# 数据输出速率常量
RATE_0_625_HZ = const(0b000000)  # 0.625 Hz
RATE_1_25_HZ = const(0b000010)  # 1.25 Hz
RATE_2_5_HZ = const(0b000100)  # 2.5 Hz
RATE_5_HZ = const(0b000110)  # 5 Hz
RATE_10_HZ = const(0b001000)  # 10 Hz
RATE_20_HZ = const(0b001010)  # 20 Hz
RATE_40_HZ = const(0b001100)  # 40 Hz
RATE_80_HZ = const(0b001110)  # 80 Hz
RATE_155_HZ = const(0b000001)  # 155 Hz (需配合FAST_ODR)
RATE_300_HZ = const(0b010001)  # 300 Hz (需配合FAST_ODR)
RATE_560_HZ = const(0b100001)  # 560 Hz (需配合FAST_ODR)
RATE_1000_HZ = const(0b110001)  # 1000 Hz (需配合FAST_ODR)
data_rate_values = (
    RATE_0_625_HZ,
    RATE_1_25_HZ,
    RATE_2_5_HZ,
    RATE_5_HZ,
    RATE_10_HZ,
    RATE_20_HZ,
    RATE_40_HZ,
    RATE_80_HZ,
    RATE_155_HZ,
    RATE_300_HZ,
    RATE_560_HZ,
    RATE_1000_HZ,
)

# 磁力计量程常量
SCALE_4_GAUSS = const(0b00)  # ±4高斯
SCALE_8_GAUSS = const(0b01)  # ±8高斯
SCALE_12_GAUSS = const(0b10)  # ±12高斯
SCALE_16_GAUSS = const(0b11)  # ±16高斯
scale_range_values = (SCALE_4_GAUSS, SCALE_8_GAUSS, SCALE_12_GAUSS, SCALE_16_GAUSS)
# 量程对应的转换因子（用于原始数据到高斯的转换）
scale_range_factor = {
    SCALE_4_GAUSS: 6842,
    SCALE_8_GAUSS: 3421,
    SCALE_12_GAUSS: 2281,
    SCALE_16_GAUSS: 1711,
}

# 低功耗模式常量
LP_DISABLED = const(0b0)  # 禁用低功耗模式，取值0
LP_ENABLED = const(0b1)  # 启用低功耗模式，取值1
low_power_mode_values = (LP_DISABLED, LP_ENABLED)

# 工作模式常量
CONTINUOUS = const(0b00)  # 连续测量模式，取值0
ONE_SHOT = const(0b01)  # 单次测量模式，取值1
POWER_DOWN = const(0b10)  # 掉电模式，取值2
operation_mode_values = (CONTINUOUS, ONE_SHOT, POWER_DOWN)


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class LIS3MDL:
    """
    基于I2C的LIS3MDL磁力计传感器驱动类

    Attributes:
        _i2c (I2C): I2C总线对象
        _address (int): 设备I2C地址
        _scale_cached_factor (int): 当前量程对应的转换因子缓存

    Methods:
        __init__(): 初始化传感器并验证器件ID
        reset(): 复位传感器
        data_rate(): 获取/设置数据输出速率
        scale_range(): 获取/设置量程
        low_power_mode(): 获取/设置低功耗模式
        operation_mode(): 获取/设置工作模式
        magnetic(): 读取磁力计数据（微特斯拉）

    Notes:
        数据速率高于80Hz时需要同时激活FAST_ODR位并正确设置X/Y轴工作模式，请参考数据手册。

    ==========================================
    Driver class for the LIS3MDL magnetometer sensor connected over I2C.

    Attributes:
        _i2c (I2C): I2C bus object
        _address (int): I2C device address
        _scale_cached_factor (int): Cached conversion factor for current scale range

    Methods:
        __init__(): Initialize sensor and verify device ID
        reset(): Reset the sensor
        data_rate(): Get/set data output rate
        scale_range(): Get/set measurement scale range
        low_power_mode(): Get/set low power mode
        operation_mode(): Get/set operation mode
        magnetic(): Read magnetometer data in microteslas

    Notes:
        Data rates higher than 80 Hz require enabling FAST_ODR bit and setting
        X/Y axes operative mode correctly. Refer to the datasheet.
    """

    _device_id = RegisterStruct(_REG_WHO_AM_I, "B")
    _data_rate = CBits(6, _CTRL_REG1, 1)
    _scale_range = CBits(2, _CTRL_REG2, 5)
    _reset = CBits(1, _CTRL_REG2, 2)
    _low_power_mode = CBits(1, _CTRL_REG3, 5)
    _operation_mode = CBits(2, _CTRL_REG3, 0)
    _raw_magnetic_data = RegisterStruct(_DATA, "<hhh")

    def __init__(self, i2c, address: int = 0x1C) -> None:
        """
        初始化LIS3MDL传感器

        Args:
            i2c (I2C): 已配置的machine.I2C对象
            address (int): 设备I2C地址，默认为0x1C

        Raises:
            ValueError: 参数为None或类型/地址无效时
            RuntimeError: 未找到传感器（器件ID不匹配）

        Notes:
            初始化后会将工作模式设为连续测量模式，并缓存当前量程的转换因子。

        ==========================================
        Initialize the LIS3MDL sensor

        Args:
            i2c (I2C): Configured machine.I2C object
            address (int): I2C device address, defaults to 0x1C

        Raises:
            ValueError: When any parameter is None or invalid type/address
            RuntimeError: When sensor is not found (device ID mismatch)

        Notes:
            After initialization, operation mode is set to continuous mode and
            the conversion factor for the current scale range is cached.
        """
        # 参数None检查
        if i2c is None:
            raise ValueError("I2C bus cannot be None")
        if address is None:
            raise ValueError("I2C address cannot be None")

        # 类型验证
        if not hasattr(i2c, "readfrom_mem") and not hasattr(i2c, "writeto_mem"):
            raise TypeError("i2c must be a valid I2C object with mem methods")
        if not isinstance(address, int):
            raise TypeError(f"Address must be integer, got {type(address).__name__}")

        # 取值范围验证
        if address < 0x08 or address > 0x77:
            raise ValueError(f"I2C address 0x{address:02X} is out of valid range (0x08-0x77)")

        self._i2c = i2c
        self._address = address

        # 验证器件ID
        if self._device_id != 0x3D:
            raise RuntimeError("Failed to find the LIS3MDL sensor")

        # 设置工作模式为连续测量
        self._operation_mode = CONTINUOUS
        # 缓存当前量程的转换因子
        self._scale_cached_factor = scale_range_factor[self._scale_range]

    @property
    def data_rate(self) -> str:
        """
        获取当前数据输出速率（字符串描述）

        Returns:
            str: 速率模式名称，如"RATE_10_HZ"

        Notes:
            返回的字符串对应预定义的速率常量名称。

        ==========================================
        Get current data output rate as string description

        Returns:
            str: Rate mode name, e.g., "RATE_10_HZ"

        Notes:
            The returned string corresponds to one of the predefined rate constants.
        """
        values = (
            "RATE_0_625_HZ",
            "RATE_1_25_HZ",
            "RATE_2_5_HZ",
            "RATE_5_HZ",
            "RATE_10_HZ",
            "RATE_20_HZ",
            "RATE_40_HZ",
            "RATE_80_HZ",
            "RATE_155_HZ",
            "RATE_300_HZ",
            "RATE_560_HZ",
            "RATE_1000_HZ",
        )
        return values[self._data_rate]

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        """
        设置数据输出速率

        Args:
            value (int): 速率常量，必须为data_rate_values中的值

        Raises:
            ValueError: 参数为None或不在有效范围内

        Notes:
            速率高于80Hz时需要配合FAST_ODR位和X/Y轴工作模式设置。

        ==========================================
        Set data output rate

        Args:
            value (int): Rate constant, must be one of data_rate_values

        Raises:
            ValueError: When value is None or not in valid range

        Notes:
            Rates higher than 80 Hz require setting FAST_ODR bit and X/Y axes mode.
        """
        # 参数None检查
        if value is None:
            raise ValueError("Data rate value cannot be None")
        # 类型验证
        if not isinstance(value, int):
            raise TypeError(f"Data rate must be integer, got {type(value).__name__}")
        # 取值范围验证
        if value not in data_rate_values:
            raise ValueError("Value must be a valid data_rate setting")
        self._data_rate = value

    @property
    def scale_range(self) -> str:
        """
        获取当前量程（字符串描述）

        Returns:
            str: 量程模式名称，如"SCALE_4_GAUSS"

        ==========================================
        Get current scale range as string description

        Returns:
            str: Scale range name, e.g., "SCALE_4_GAUSS"
        """
        values = ("SCALE_4_GAUSS", "SCALE_8_GAUSS", "SCALE_12_GAUSS", "SCALE_16_GAUSS")
        return values[self._scale_range]

    @scale_range.setter
    def scale_range(self, value: int) -> None:
        """
        设置磁力计量程

        Args:
            value (int): 量程常量，必须为scale_range_values中的值

        Raises:
            ValueError: 参数为None或不在有效范围内

        Notes:
            改变量程后会同步更新内部转换因子缓存。

        ==========================================
        Set magnetometer scale range

        Args:
            value (int): Scale constant, must be one of scale_range_values

        Raises:
            ValueError: When value is None or not in valid range

        Notes:
            The internal conversion factor cache is updated when scale changes.
        """
        # 参数None检查
        if value is None:
            raise ValueError("Scale range value cannot be None")
        # 类型验证
        if not isinstance(value, int):
            raise TypeError(f"Scale range must be integer, got {type(value).__name__}")
        # 取值范围验证
        if value not in scale_range_values:
            raise ValueError("Value must be a valid scale_range setting")
        self._scale_range = value
        self._scale_cached_factor = scale_range_factor[value]

    def reset(self) -> None:
        """
        复位传感器

        Notes:
            将复位位置1，然后等待10ms以确保复位完成。

        ==========================================
        Reset the sensor

        Notes:
            Sets the reset bit and waits 10ms for completion.
        """
        self._reset = True
        time.sleep(0.010)

    @property
    def low_power_mode(self) -> str:
        """
        获取当前低功耗模式状态（字符串描述）

        Returns:
            str: "LP_DISABLED" 或 "LP_ENABLED"

        Notes:
            默认值为禁用（LP_DISABLED）。启用后数据速率会被强制设为0.625Hz。

        ==========================================
        Get current low power mode status as string description

        Returns:
            str: Either "LP_DISABLED" or "LP_ENABLED"

        Notes:
            Default is disabled. When enabled, data rate is forced to 0.625 Hz.
        """
        values = ("LP_DISABLED", "LP_ENABLED")
        return values[self._low_power_mode]

    @low_power_mode.setter
    def low_power_mode(self, value: int) -> None:
        """
        设置低功耗模式

        Args:
            value (int): 低功耗模式常量，必须为low_power_mode_values中的值

        Raises:
            ValueError: 参数为None或不在有效范围内

        ==========================================
        Set low power mode

        Args:
            value (int): Low power mode constant, must be one of low_power_mode_values

        Raises:
            ValueError: When value is None or not in valid range
        """
        # 参数None检查
        if value is None:
            raise ValueError("Low power mode value cannot be None")
        # 类型验证
        if not isinstance(value, int):
            raise TypeError(f"Low power mode must be integer, got {type(value).__name__}")
        # 取值范围验证
        if value not in low_power_mode_values:
            raise ValueError("Value must be a valid low_power_mode setting")
        self._low_power_mode = value

    @property
    def operation_mode(self) -> str:
        """
        获取当前工作模式（字符串描述）

        Returns:
            str: "CONTINUOUS", "ONE_SHOT" 或 "POWER_DOWN"

        ==========================================
        Get current operation mode as string description

        Returns:
            str: "CONTINUOUS", "ONE_SHOT" or "POWER_DOWN"
        """
        values = ("CONTINUOUS", "ONE_SHOT", "POWER_DOWN")
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        """
        设置工作模式

        Args:
            value (int): 工作模式常量，必须为operation_mode_values中的值

        Raises:
            ValueError: 参数为None或不在有效范围内

        ==========================================
        Set operation mode

        Args:
            value (int): Operation mode constant, must be one of operation_mode_values

        Raises:
            ValueError: When value is None or not in valid range
        """
        # 参数None检查
        if value is None:
            raise ValueError("Operation mode value cannot be None")
        # 类型验证
        if not isinstance(value, int):
            raise TypeError(f"Operation mode must be integer, got {type(value).__name__}")
        # 取值范围验证
        if value not in operation_mode_values:
            raise ValueError("Value must be a valid operation_mode setting")
        self._operation_mode = value

    @property
    def magnetic(self) -> Tuple[float, float, float]:
        """
        读取磁力计数据（微特斯拉）

        Returns:
            Tuple[float, float, float]: (X轴, Y轴, Z轴) 磁场强度，单位μT

        Notes:
            原始数据根据当前量程的转换因子和高斯-微特斯拉系数进行换算。

        ==========================================
        Read magnetometer data in microteslas

        Returns:
            Tuple[float, float, float]: (X-axis, Y-axis, Z-axis) magnetic field in μT

        Notes:
            Raw data is converted using the current scale range conversion factor
            and Gauss-to-microtesla multiplier.
        """
        rawx, rawy, rawz = self._raw_magnetic_data
        x = rawx / self._scale_cached_factor * _GAUSS_TO_UT
        y = rawy / self._scale_cached_factor * _GAUSS_TO_UT
        z = rawz / self._scale_cached_factor * _GAUSS_TO_UT
        return x, y, z


# ======================================== 初始化配置 ============================================

# ======================================== 主程序 ============================================
