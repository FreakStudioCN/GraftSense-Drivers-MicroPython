# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Jose D. Montoya
# @File    : lis2mdl.py
# @Description : STLIS2MDL磁力计传感器的MicroPython驱动库
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

import time
from collections import namedtuple
from micropython import const
from micropython_lis2mdl.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass


# ======================================== 全局变量 ============================================

# 中断阈值低字节寄存器地址
INT_THS_L_REG = 0x65
# 器件WHO_AM_I寄存器地址
_REG_WHO_AM_I = const(0x4F)
# 配置寄存器A地址
_CFG_REG_A = const(0x60)
# 配置寄存器B地址
_CFG_REG_B = const(0x61)
# 配置寄存器C地址
_CFG_REG_C = const(0x62)
# 中断控制寄存器地址
_INT_CRTL_REG = const(0x63)
# 中断源寄存器地址
_INT_SOURCE_REG = const(0x64)
# 中断阈值寄存器地址
_INT_THS = const(0x65)
# 数据寄存器起始地址
_DATA = const(0x68)

# 高斯到微特斯拉转换系数
_GAUSS_TO_UT = 0.15

# 连续测量模式常量
CONTINUOUS = const(0b00)
# 单次测量模式常量
ONE_SHOT = const(0b01)
# 断电模式常量
POWER_DOWN = const(0b10)
# 有效操作模式值元组
operation_mode_values = (CONTINUOUS, ONE_SHOT, POWER_DOWN)

# 10Hz数据速率常量
RATE_10_HZ = const(0b00)
# 20Hz数据速率常量
RATE_20_HZ = const(0b01)
# 50Hz数据速率常量
RATE_50_HZ = const(0b10)
# 100Hz数据速率常量
RATE_100_HZ = const(0b11)
# 有效数据速率值元组
data_rate_values = (RATE_10_HZ, RATE_20_HZ, RATE_50_HZ, RATE_100_HZ)

# 低功耗模式禁用常量
LP_DISABLED = const(0b0)
# 低功耗模式使能常量
LP_ENABLED = const(0b1)
# 有效低功耗模式值元组
low_power_mode_values = (LP_DISABLED, LP_ENABLED)

# 低通滤波器禁用常量
LPF_DISABLED = const(0b0)
# 低通滤波器使能常量
LPF_ENABLED = const(0b1)
# 有效低通滤波器模式值元组
low_pass_filter_mode_values = (LPF_DISABLED, LPF_ENABLED)

# 中断禁用常量
INT_DISABLED = const(0b0)
# 中断使能常量
INT_ENABLED = const(0b1)
# 有效中断模式值元组
interrupt_mode_values = (INT_DISABLED, INT_ENABLED)


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 告警状态命名元组定义
AlertStatus = namedtuple("AlertStatus", ["x_high", "x_low", "y_high", "y_low", "z_high", "z_low"])


class LIS2MDL:
    """
    LIS2MDL磁力计传感器驱动类
    Attributes:
        _i2c (I2C): I2C总线对象
        _address (int): 设备I2C地址

    Methods:
        reset(): 复位传感器
        magnetic(): 获取磁场数据

    Notes:
        默认I2C地址为0x1E

    ==========================================
    Driver class for LIS2MDL magnetometer sensor
    Attributes:
        _i2c (I2C): I2C bus object
        _address (int): Device I2C address

    Methods:
        reset(): Reset the sensor
        magnetic(): Get magnetic data

    Notes:
        Default I2C address is 0x1E
    """

    # WHO_AM_I寄存器结构
    _device_id = RegisterStruct(_REG_WHO_AM_I, "B")

    # 复位控制位
    _reset = CBits(1, _CFG_REG_A, 5)
    # 低功耗模式控制位
    _low_power_mode = CBits(1, _CFG_REG_A, 4)
    # 数据速率控制位
    _data_rate = CBits(2, _CFG_REG_A, 2)
    # 操作模式控制位
    _operation_mode = CBits(2, _CFG_REG_A, 0)

    # 低通滤波器模式控制位
    _low_pass_filter_mode = CBits(1, _CFG_REG_B, 0)

    # XYZ轴中断使能控制位
    _xyz_interrupt_enable = CBits(3, _INT_CRTL_REG, 5)
    # 中断引脚极性控制位
    _int_reg_polarity = CBits(1, _INT_CRTL_REG, 2)
    # 中断锁存控制位
    _int_latched = CBits(1, _INT_CRTL_REG, 1)
    # 中断模式控制位
    _interrupt_mode = CBits(1, _INT_CRTL_REG, 0)
    # 中断引脚反相控制位
    _interrupt_pin_inversed = CBits(1, _CFG_REG_C, 6)
    # 中断控制寄存器信息
    information_about_interrup = RegisterStruct(_INT_CRTL_REG, "B")

    # X轴高阈值中断标志位
    _x_high = CBits(1, _INT_SOURCE_REG, 7)
    # Y轴高阈值中断标志位
    _y_high = CBits(1, _INT_SOURCE_REG, 6)
    # Z轴高阈值中断标志位
    _z_high = CBits(1, _INT_SOURCE_REG, 5)
    # X轴低阈值中断标志位
    _x_low = CBits(1, _INT_SOURCE_REG, 4)
    # Y轴低阈值中断标志位
    _y_low = CBits(1, _INT_SOURCE_REG, 3)
    # Z轴低阈值中断标志位
    _z_low = CBits(1, _INT_SOURCE_REG, 2)
    # 中断触发标志位
    _interrupt_triggered = CBits(1, _INT_SOURCE_REG, 0)
    # 中断源寄存器信息
    need = RegisterStruct(_INT_SOURCE_REG, "B")

    # 原始磁场数据寄存器结构
    _raw_magnetic_data = RegisterStruct(_DATA, "<hhh")
    # 中断阈值寄存器结构
    _interrupt_threshold = RegisterStruct(INT_THS_L_REG, "<h")

    def __init__(self, i2c, address: int = 0x1E) -> None:
        """
        初始化LIS2MDL传感器
        Args:
            i2c (I2C): I2C总线对象
            address (int): 设备I2C地址，默认0x1E

        Raises:
            RuntimeError: 未找到传感器设备时抛出

        Notes:
            初始化后自动设置为连续测量模式

        ==========================================
        Initialize LIS2MDL sensor
        Args:
            i2c (I2C): I2C bus object
            address (int): Device I2C address, default 0x1E

        Raises:
            RuntimeError: Raised when sensor device not found

        Notes:
            Automatically set to continuous mode after initialization
        """
        self._i2c = i2c
        self._address = address

        # 检查器件ID是否正确
        if self._device_id != 0x40:
            raise RuntimeError("Failed to find the LIS2MDL sensor")

        # 设置默认配置：连续模式、中断锁存使能、中断极性高有效、中断引脚非反相
        self._operation_mode = CONTINUOUS
        self._int_latched = True
        self._int_reg_polarity = True
        self._interrupt_pin_inversed = True

    @property
    def operation_mode(self) -> str:
        """
        获取当前操作模式
        Returns:
            str: 操作模式字符串

        Notes:
            返回值对应: CONTINUOUS/ONE_SHOT/POWER_DOWN

        ==========================================
        Get current operation mode
        Returns:
            str: Operation mode string

        Notes:
            Return values: CONTINUOUS/ONE_SHOT/POWER_DOWN
        """
        values = ("CONTINUOUS", "ONE_SHOT", "POWER_DOWN")
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        """
        设置操作模式
        Args:
            value (int): 操作模式值

        Raises:
            ValueError: 值无效时抛出

        Notes:
            有效值见operation_mode_values

        ==========================================
        Set operation mode
        Args:
            value (int): Operation mode value

        Raises:
            ValueError: Raised when value is invalid

        Notes:
            Valid values see operation_mode_values
        """
        if value not in operation_mode_values:
            raise ValueError("Value must be a valid operation_mode setting")
        self._operation_mode = value

    @property
    def data_rate(self) -> str:
        """
        获取当前数据速率
        Returns:
            str: 数据速率字符串

        Notes:
            返回值对应: RATE_10_HZ/RATE_20_HZ/RATE_50_HZ/RATE_100_HZ

        ==========================================
        Get current data rate
        Returns:
            str: Data rate string

        Notes:
            Return values: RATE_10_HZ/RATE_20_HZ/RATE_50_HZ/RATE_100_HZ
        """
        values = ("RATE_10_HZ", "RATE_20_HZ", "RATE_50_HZ", "RATE_100_HZ")
        return values[self._data_rate]

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        """
        设置数据速率
        Args:
            value (int): 数据速率值

        Raises:
            ValueError: 值无效时抛出

        Notes:
            有效值见data_rate_values

        ==========================================
        Set data rate
        Args:
            value (int): Data rate value

        Raises:
            ValueError: Raised when value is invalid

        Notes:
            Valid values see data_rate_values
        """
        if value not in data_rate_values:
            raise ValueError("Value must be a valid data_rate setting")
        self._data_rate = value

    def reset(self) -> None:
        """
        复位传感器
        Notes:
            复位后等待10ms确保完成

        ==========================================
        Reset the sensor
        Notes:
            Wait 10ms after reset to ensure completion
        """
        self._reset = True
        time.sleep(0.010)

    @property
    def low_power_mode(self) -> str:
        """
        获取低功耗模式状态
        Returns:
            str: 低功耗模式字符串

        Notes:
            返回值对应: LP_DISABLED/LP_ENABLED

        ==========================================
        Get low power mode status
        Returns:
            str: Low power mode string

        Notes:
            Return values: LP_DISABLED/LP_ENABLED
        """
        values = ("LP_DISABLED", "LP_ENABLED")
        return values[self._low_power_mode]

    @low_power_mode.setter
    def low_power_mode(self, value: int) -> None:
        """
        设置低功耗模式
        Args:
            value (int): 低功耗模式值

        Raises:
            ValueError: 值无效时抛出

        Notes:
            有效值见low_power_mode_values

        ==========================================
        Set low power mode
        Args:
            value (int): Low power mode value

        Raises:
            ValueError: Raised when value is invalid

        Notes:
            Valid values see low_power_mode_values
        """
        if value not in low_power_mode_values:
            raise ValueError("Value must be a valid low_power_mode setting")
        self._low_power_mode = value

    @property
    def magnetic(self) -> Tuple[float, float, float]:
        """
        获取磁场数据
        Returns:
            Tuple[float, float, float]: X, Y, Z轴磁场值(微特斯拉)

        Notes:
            数据单位为微特斯拉(uT)

        ==========================================
        Get magnetic data
        Returns:
            Tuple[float, float, float]: X, Y, Z magnetic values (microteslas)

        Notes:
            Unit is microtesla (uT)
        """
        rawx, rawy, rawz = self._raw_magnetic_data
        x = rawx * _GAUSS_TO_UT
        y = rawy * _GAUSS_TO_UT
        z = rawz * _GAUSS_TO_UT

        return x, y, z

    @property
    def low_pass_filter_mode(self) -> str:
        """
        获取低通滤波器模式
        Returns:
            str: 低通滤波器模式字符串

        Notes:
            返回值对应: LPF_DISABLED/LPF_ENABLED

        ==========================================
        Get low pass filter mode
        Returns:
            str: Low pass filter mode string

        Notes:
            Return values: LPF_DISABLED/LPF_ENABLED
        """
        values = ("LPF_DISABLED", "LPF_ENABLED")
        return values[self._low_pass_filter_mode]

    @low_pass_filter_mode.setter
    def low_pass_filter_mode(self, value: int) -> None:
        """
        设置低通滤波器模式
        Args:
            value (int): 低通滤波器模式值

        Raises:
            ValueError: 值无效时抛出

        Notes:
            有效值见low_pass_filter_mode_values

        ==========================================
        Set low pass filter mode
        Args:
            value (int): Low pass filter mode value

        Raises:
            ValueError: Raised when value is invalid

        Notes:
            Valid values see low_pass_filter_mode_values
        """
        if value not in low_pass_filter_mode_values:
            raise ValueError("Value must be a valid low_pass_filter_mode setting")
        self._low_pass_filter_mode = value

    @property
    def interrupt_mode(self) -> str:
        """
        获取中断模式状态
        Returns:
            str: 中断模式字符串

        Notes:
            返回值对应: INT_DISABLED/INT_ENABLED

        ==========================================
        Get interrupt mode status
        Returns:
            str: Interrupt mode string

        Notes:
            Return values: INT_DISABLED/INT_ENABLED
        """
        values = ("INT_DISABLED", "INT_ENABLED")
        return values[self._interrupt_mode]

    @interrupt_mode.setter
    def interrupt_mode(self, value: int) -> None:
        """
        设置中断模式
        Args:
            value (int): 中断模式值

        Raises:
            ValueError: 值无效时抛出

        Notes:
            使能时自动使能XYZ轴中断

        ==========================================
        Set interrupt mode
        Args:
            value (int): Interrupt mode value

        Raises:
            ValueError: Raised when value is invalid

        Notes:
            Automatically enable XYZ interrupts when enabled
        """
        if value not in interrupt_mode_values:
            raise ValueError("Value must be a valid interrupt_mode setting")
        self._interrupt_mode = value
        if value:
            self._xyz_interrupt_enable = 0b111
        else:
            self._xyz_interrupt_enable = 0

    @property
    def interrupt_threshold(self) -> float:
        """
        获取中断阈值
        Returns:
            float: 中断阈值(微特斯拉)

        Notes:
            阈值应用于所有轴的正负方向比较

        ==========================================
        Get interrupt threshold
        Returns:
            float: Interrupt threshold (microteslas)

        Notes:
            Threshold applies to both positive and negative directions of all axes
        """
        return self._interrupt_threshold * _GAUSS_TO_UT

    @interrupt_threshold.setter
    def interrupt_threshold(self, value: float) -> None:
        """
        设置中断阈值
        Args:
            value (float): 中断阈值(微特斯拉)

        Notes:
            负值会被转换为正值

        ==========================================
        Set interrupt threshold
        Args:
            value (float): Interrupt threshold (microteslas)

        Notes:
            Negative values will be converted to positive
        """
        if value < 0:
            value = -value
        self._interrupt_threshold = int(value / _GAUSS_TO_UT)

    @property
    def interrupt_triggered(self):
        """
        检查中断是否触发
        Returns:
            bool: 中断触发状态

        Notes:
            读取后自动清除中断标志

        ==========================================
        Check if interrupt is triggered
        Returns:
            bool: Interrupt triggered status

        Notes:
            Interrupt flag is automatically cleared after read
        """
        return self._interrupt_triggered

    @property
    def alert_status(self):
        """
        获取告警状态
        Returns:
            AlertStatus: 包含各轴高低阈值告警状态的命名元组

        Notes:
            返回各轴的独立告警状态

        ==========================================
        Get alert status
        Returns:
            AlertStatus: Namedtuple containing high/low threshold alert status for each axis

        Notes:
            Returns independent alert status for each axis
        """
        return AlertStatus(
            x_high=self._x_high,
            x_low=self._x_low,
            y_high=self._y_high,
            y_low=self._y_low,
            z_high=self._z_high,
            z_low=self._z_low,
        )


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
