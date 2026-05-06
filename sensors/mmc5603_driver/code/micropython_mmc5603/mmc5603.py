# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/18 下午2:15
# @Author  : Jose D. Montoya
# @File    : mmc5603.py
# @Description : MMC5603磁力计MicroPython驱动，提供磁场和温度测量功能
# @License : MIT
__version__ = "0.0.0+auto.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const
from micropython_mmc5603.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass

# ======================================== 全局变量 ============================================

# 器件标识寄存器地址
_REG_WHOIAM = const(0x39)
# 数据寄存器起始地址
_DATA = const(0x00)
# 温度寄存器地址
_TEMP = const(0x09)
# 状态寄存器地址
_STATUS_REG = const(0x18)
# 输出数据速率寄存器地址
_ODR_REG = const(0x1A)
# 控制寄存器0地址
_CTRL_REG0 = const(0x1B)
# 控制寄存器1地址
_CTRL_REG1 = const(0x1C)
# 控制寄存器2地址
_CTRL_REG2 = const(0x1D)

# 测量时间配置常量
# 6.6ms测量时间
MT_6_6ms = const(0b00)
# 3.5ms测量时间
MT_3_5ms = const(0b01)
# 2.0ms测量时间
MT_2_0ms = const(0b10)
# 1.2ms测量时间
MT_1_2ms = const(0b11)
measure_time_values = (MT_6_6ms, MT_3_5ms, MT_2_0ms, MT_1_2ms)

# ======================================== 自定义类 ============================================


class MMC5603:
    """
    MMC5603磁力计驱动类，通过I2C接口进行磁场和温度测量。

    Attributes:
        _i2c (I2C): I2C总线对象
        _address (int): 设备I2C地址，默认0x30
        _ctrl2_cache (int): 控制寄存器2的缓存值
        _odr_cache (int): 输出数据速率缓存值
        _measure_time_cached (int): 测量时间配置缓存值
        _buffer (bytearray): 数据读取缓冲区(9字节)
        _device_id (RegisterStruct): 器件标识寄存器结构
        _ctrl0_reg (RegisterStruct): 控制寄存器0结构
        _ctrl1_reg (RegisterStruct): 控制寄存器1结构
        _ctrl2_reg (RegisterStruct): 控制寄存器2结构
        _odr_reg (RegisterStruct): 输出数据速率寄存器结构
        _raw_temp_data (RegisterStruct): 原始温度数据寄存器结构
        _meas_m_done (CBits): 磁场测量完成标志位
        _meas_t_done (CBits): 温度测量完成标志位

    Methods:
        magnetic(): 读取磁场强度(微特斯拉)
        temperature(): 读取温度值(摄氏度)
        data_rate(): 设置/获取输出数据速率
        continuous_mode(): 设置/获取连续测量模式
        measure_time(): 设置/获取测量时间配置

    Notes:
        基于I2C通信，支持单次和连续测量模式，测量前需进行复位和自动设置操作。

    ==========================================
    Driver class for MMC5603 magnetometer via I2C.

    Attributes:
        _i2c (I2C): I2C bus object
        _address (int): I2C device address, default 0x30
        _ctrl2_cache (int): Cached value of control register 2
        _odr_cache (int): Cached output data rate value
        _measure_time_cached (int): Cached measurement time setting
        _buffer (bytearray): Data read buffer (9 bytes)
        _device_id (RegisterStruct): Device ID register structure
        _ctrl0_reg (RegisterStruct): Control register 0 structure
        _ctrl1_reg (RegisterStruct): Control register 1 structure
        _ctrl2_reg (RegisterStruct): Control register 2 structure
        _odr_reg (RegisterStruct): Output data rate register structure
        _raw_temp_data (RegisterStruct): Raw temperature data register structure
        _meas_m_done (CBits): Magnetic measurement done flag
        _meas_t_done (CBits): Temperature measurement done flag

    Methods:
        magnetic(): Read magnetic field strength (microteslas)
        temperature(): Read temperature value (Celsius)
        data_rate(): Get/set output data rate
        continuous_mode(): Get/set continuous measurement mode
        measure_time(): Get/set measurement time configuration

    Notes:
        I2C-based communication, supports single-shot and continuous modes.
        Reset and auto-set operations are performed during initialization.
    """

    _device_id = RegisterStruct(_REG_WHOIAM, "<B")
    _ctrl0_reg = RegisterStruct(_CTRL_REG0, "<B")
    _ctrl1_reg = RegisterStruct(_CTRL_REG1, "<B")
    _ctrl2_reg = RegisterStruct(_CTRL_REG2, "B")

    _odr_reg = RegisterStruct(_ODR_REG, "<B")
    _raw_temp_data = RegisterStruct(_TEMP, "B")

    _meas_m_done = CBits(1, _STATUS_REG, 6)
    _meas_t_done = CBits(1, _STATUS_REG, 7)

    def __init__(self, i2c, address: int = 0x30) -> None:
        """
        初始化MMC5603传感器，配置I2C接口并进行复位和自动设置。

        Args:
            i2c (I2C): 已初始化的machine.I2C对象
            address (int): 设备I2C地址，取值范围0x30或0x38，默认0x30

        Raises:
            ValueError: i2c参数为None或address类型/范围无效
            TypeError: address不是整数类型
            RuntimeError: 无法找到MMC5603设备(器件ID不匹配)

        Notes:
            执行复位(Do_Reset)和自动设置(Do_Set)操作，耗时约22ms。

        ==========================================
        Initialize MMC5603 sensor, configure I2C interface and perform reset/auto-set.

        Args:
            i2c (I2C): Initialized machine.I2C object
            address (int): I2C device address, valid values 0x30 or 0x38, default 0x30

        Raises:
            ValueError: i2c parameter is None or address type/range invalid
            TypeError: address is not integer
            RuntimeError: Failed to find MMC5603 device (device ID mismatch)

        Notes:
            Performs Do_Reset and Do_Set operations, takes about 22ms.
        """
        # 参数验证
        if i2c is None:
            raise ValueError("I2C object cannot be None")
        if not isinstance(address, int):
            raise TypeError("Address must be an integer")
        if address not in (0x30, 0x38):
            raise ValueError("Address must be 0x30 or 0x38")

        self._i2c = i2c
        self._address = address

        # 检查器件ID
        if self._device_id != 0x10:
            raise RuntimeError("Failed to find MMC5603")

        self._ctrl2_cache = 0
        self._odr_cache = 0
        self._measure_time_cached = 0

        # 分配数据缓冲区
        self._buffer = bytearray(9)

        # 配置控制寄存器1
        self._ctrl1_reg = 0x80
        time.sleep(0.020)
        # 执行Do_Set操作
        self._ctrl0_reg = 0x08
        time.sleep(0.001)
        # 执行Do_Reset操作
        self._ctrl0_reg = 0x10
        time.sleep(0.001)
        # 设置为自动Do_Set-Do_Reset模式
        self._ctrl0_reg = 0x20
        time.sleep(0.001)

    @property
    def magnetic(self) -> Tuple[float, float, float]:
        """
        读取磁场强度数据(微特斯拉)。

        Returns:
            Tuple[float, float, float]: 包含X、Y、Z轴磁场强度的三元组，单位μT

        Notes:
            非连续模式下会触发单次测量并等待完成；连续模式下直接读取最新数据。
            数据范围为±16384μT，分辨率0.00625μT/LSB。

        ==========================================
        Read magnetic field strength data (microteslas).

        Returns:
            Tuple[float, float, float]: Tuple of X, Y, Z axis magnetic field strength in μT

        Notes:
            In non-continuous mode, triggers a single measurement and waits for completion.
            In continuous mode, reads the latest data directly.
            Range ±16384μT, resolution 0.00625μT/LSB.
        """
        # 非连续模式下触发单次测量
        if not self.continuous_mode:
            self._ctrl0_reg = 0x01
            # 等待测量完成
            while not self._meas_m_done:
                time.sleep(0.005)

        # 读取9字节原始数据
        self._i2c.readfrom_mem_into(self._address, _DATA, self._buffer)

        # 解包20位数据(每轴3字节拼接)
        x = self._buffer[0] << 12 | self._buffer[1] << 4 | self._buffer[6] >> 4
        y = self._buffer[2] << 12 | self._buffer[3] << 4 | self._buffer[7] >> 4
        z = self._buffer[4] << 12 | self._buffer[5] << 4 | self._buffer[8] >> 4

        # 转换为有符号20位整数
        x -= 1 << 19
        y -= 1 << 19
        z -= 1 << 19
        # 缩放至微特斯拉
        x *= 0.00625
        y *= 0.00625
        z *= 0.00625
        return x, y, z

    @property
    def temperature(self) -> float:
        """
        读取温度传感器数据(摄氏度)。

        Returns:
            float: 温度值，单位℃

        Raises:
            RuntimeError: 连续模式下无法读取温度(需切换至单次模式)

        Notes:
            仅支持单次测量模式，连续模式下需先禁用连续模式。

        ==========================================
        Read temperature sensor data (Celsius).

        Returns:
            float: Temperature value in ℃

        Raises:
            RuntimeError: Cannot read temperature in continuous mode (switch to single-shot mode)

        Notes:
            Only supported in single-shot mode. Disable continuous mode first.
        """
        # 连续模式下禁止读取温度
        if self.continuous_mode:
            raise RuntimeError("Can only read temperature when not in continuous mode")
        # 触发温度测量
        self._ctrl0_reg = 0x02
        # 等待测量完成
        while not self._meas_t_done:
            time.sleep(0.005)
        temp = self._raw_temp_data
        # 转换为摄氏度: T = 0.8 * TEMP_OUT - 75
        temp *= 0.8
        temp -= 75
        return temp

    @property
    def data_rate(self) -> int:
        """
        获取输出数据速率(Hz)。

        Returns:
            int: 数据速率值，0表示单次测量，1-255表示对应频率，1000表示1000Hz

        ==========================================
        Get output data rate (Hz).

        Returns:
            int: Data rate value, 0 for single-shot, 1-255 for corresponding frequency, 1000 for 1000Hz
        """
        return self._odr_cache

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        """
        设置输出数据速率(Hz)。

        Args:
            value (int): 数据速率，允许值: 0(单次), 1-255(对应Hz), 1000(1000Hz)

        Raises:
            ValueError: value为None或不在允许范围内
            TypeError: value不是整数类型

        Notes:
            设置1000Hz时会自动开启高功率模式(HPower)。

        ==========================================
        Set output data rate (Hz).

        Args:
            value (int): Data rate, allowed values: 0 (single-shot), 1-255 (corresponding Hz), 1000 (1000Hz)

        Raises:
            ValueError: value is None or out of allowed range
            TypeError: value is not integer

        Notes:
            Setting 1000Hz automatically enables high power mode (HPower).
        """
        # 参数验证
        if value is None:
            raise ValueError("Data rate cannot be None")
        if not isinstance(value, int):
            raise TypeError("Data rate must be an integer")
        if not ((value == 1000) or (0 <= value <= 255)):
            raise ValueError("Data rate must be 0-255 or 1000 Hz")

        self._odr_cache = value
        if value == 1000:
            self._odr_reg = 255
            # 开启高功率位
            self._ctrl2_cache |= 0x80
            self._ctrl2_reg = self._ctrl2_cache
        else:
            self._odr_reg = value
            # 关闭高功率位
            self._ctrl2_cache &= ~0x80
            self._ctrl2_reg = self._ctrl2_cache

    @property
    def continuous_mode(self) -> bool:
        """
        获取连续测量模式状态。

        Returns:
            bool: True表示连续模式开启，False表示单次模式

        Notes:
            开启连续模式前必须设置data_rate，否则可能使用默认速率。

        ==========================================
        Get continuous measurement mode status.

        Returns:
            bool: True if continuous mode enabled, False for single-shot mode

        Notes:
            Must set data_rate before enabling continuous mode, otherwise default rate may be used.
        """
        return self._ctrl2_cache & 0x10

    @continuous_mode.setter
    def continuous_mode(self, value: bool) -> None:
        """
        设置连续测量模式。

        Args:
            value (bool): True开启连续模式，False关闭连续模式(单次模式)

        Raises:
            ValueError: value为None
            TypeError: value不是布尔类型

        Notes:
            开启时会自动设置CMM_FREQ_EN位，关闭时清除CMM_EN位。

        ==========================================
        Set continuous measurement mode.

        Args:
            value (bool): True to enable continuous mode, False to disable (single-shot mode)

        Raises:
            ValueError: value is None
            TypeError: value is not boolean

        Notes:
            Enabling automatically sets CMM_FREQ_EN bit, disabling clears CMM_EN bit.
        """
        # 参数验证
        if value is None:
            raise ValueError("Continuous mode flag cannot be None")
        if not isinstance(value, bool):
            raise TypeError("Continuous mode must be a boolean")

        if value:
            # 开启CMM_FREQ_EN位
            self._ctrl0_reg = 0x80
            # 开启CMM_EN位
            self._ctrl2_cache |= 0x10
        else:
            # 关闭CMM_EN位
            self._ctrl2_cache &= ~0x10

        self._ctrl2_reg = self._ctrl2_cache

    @property
    def measure_time(self) -> str:
        """
        获取测量时间配置(字符串描述)。

        Returns:
            str: 测量时间模式字符串，可选'MT_6_6ms','MT_3_5ms','MT_2_0ms','MT_1_2ms'

        ==========================================
        Get measurement time configuration as string.

        Returns:
            str: Measurement time mode string, options 'MT_6_6ms','MT_3_5ms','MT_2_0ms','MT_1_2ms'
        """
        values = ("MT_6_6ms", "MT_3_5ms", "MT_2_0ms", "MT_1_2ms")
        return values[self._measure_time_cached]

    @measure_time.setter
    def measure_time(self, value: int) -> None:
        """
        设置测量时间(影响测量时长和噪声性能)。

        Args:
            value (int): 测量时间常量，必须为MT_6_6ms/MT_3_5ms/MT_2_0ms/MT_1_2ms之一

        Raises:
            ValueError: value为None或不在有效常量范围内
            TypeError: value不是整数类型

        Notes:
            测量时间越短，噪声越大，适合高速应用；时间越长，噪声越小，适合高精度应用。

        ==========================================
        Set measurement time (affects measurement duration and noise performance).

        Args:
            value (int): Measurement time constant, must be one of MT_6_6ms/MT_3_5ms/MT_2_0ms/MT_1_2ms

        Raises:
            ValueError: value is None or not in valid constant range
            TypeError: value is not integer

        Notes:
            Shorter measurement time gives higher noise, suitable for high-speed applications.
            Longer measurement time gives lower noise, suitable for high-precision applications.
        """
        # 参数验证
        if value is None:
            raise ValueError("Measure time cannot be None")
        if not isinstance(value, int):
            raise TypeError("Measure time must be an integer")
        if value not in measure_time_values:
            raise ValueError("Value must be a valid measure_time setting")

        self._ctrl1_reg = value
        self._measure_time_cached = value


# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ============================================
