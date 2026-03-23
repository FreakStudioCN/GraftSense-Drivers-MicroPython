# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026-03-23 下午3:30
# @Author  : octaprog7
# @File    : sensor_base.py
# @Description : 传感器基类模块，提供I2C/SPI总线适配、寄存器访问、数据类型转换等基础功能
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# micropython
# MIT license
# Copyright (c) 2022 Roman Shevchik   goctaprog@gmail.com

# ======================================== 导入相关模块 =========================================

import struct
import micropython
from sensor_pack import bus_service
from machine import SPI

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

@micropython.native
def check_value(value: [int, None], valid_range, error_msg: str) -> [int, None]:
    """
    检查值是否在有效范围内，若值为 None 则直接返回。
    Args:
        value (int, None): 待检查的值或 None
        valid_range (iterable): 有效值范围（列表、元组等）
        error_msg (str): 值无效时抛出的异常消息

    Returns:
        int, None: 原值或 None

    Raises:
        ValueError: 当 value 不为 None 且不在 valid_range 中时

    Notes:
        若 value 为 None 则直接返回，不进行范围检查。

    ==========================================
    Check if value is in valid range; return directly if value is None.
    Args:
        value (int, None): Value to check or None
        valid_range (iterable): Valid range (list, tuple, etc.)
        error_msg (str): Exception message when value is invalid

    Returns:
        int, None: Original value or None

    Raises:
        ValueError: When value is not None and not in valid_range

    Notes:
        If value is None, returns directly without range check.
    """
    if value is None:
        return value
    if value not in valid_range:
        raise ValueError(error_msg)
    return value

# ======================================== 自定义类 ============================================

class Device:
    """
    设备基类，封装总线适配器和寄存器字节序。
    Attributes:
        adapter (bus_service.BusAdapter): 总线适配器对象（I2C/SPI）
        address (int, SPI): 设备地址（I2C 地址或 SPI 对象）
        big_byte_order (bool): 寄存器字节序，True 为大端，False 为小端
        msb_first (bool): SPI 传输时是否先发送最高有效位（默认 True）

    Methods:
        _get_byteorder_as_str(): 返回字节序字符串表示
        unpack(): 使用 struct 解包读取的字节数据
        is_big_byteorder(): 返回字节序标志

    Notes:
        I2C 设备使用地址，SPI 设备需传入 SPI 对象，同时需手动配置 msb_first。

    ==========================================
    Base device class encapsulating bus adapter and register byte order.
    Attributes:
        adapter (bus_service.BusAdapter): Bus adapter object (I2C/SPI)
        address (int, SPI): Device address (I2C address or SPI object)
        big_byte_order (bool): Register byte order, True for big-endian, False for little-endian
        msb_first (bool): Whether to send MSB first in SPI transfers (default True)

    Methods:
        _get_byteorder_as_str(): Return byte order as string representation
        unpack(): Unpack read bytes using struct
        is_big_byteorder(): Return byte order flag

    Notes:
        I2C devices use address, SPI devices pass SPI object; msb_first may need manual configuration.
    """

    def __init__(self, adapter: bus_service.BusAdapter, address: [int, SPI], big_byte_order: bool):
        """
        初始化设备实例。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int, SPI): 设备地址或 SPI 对象
            big_byte_order (bool): 寄存器字节序，True 为大端，False 为小端

        ==========================================
        Initialize device instance.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int, SPI): Device address or SPI object
            big_byte_order (bool): Register byte order, True for big-endian, False for little-endian
        """
        self.adapter = adapter
        self.address = address
        # for I2C. byte order in register of device
        self.big_byte_order = big_byte_order
        # for SPI ONLY. При передаче данных по SPI: SPI.firstbit can be SPI.MSB or SPI.LSB
        # передавать первым битом старший или младший
        # для каждого устройства!
        self.msb_first = True

    def _get_byteorder_as_str(self) -> tuple:
        """
        返回字节序字符串表示。
        Returns:
            tuple: (字节序字符串如 'big'/'little', struct 前缀如 '>'/'<')
        ==========================================
        Return byte order as string representation.
        Returns:
            tuple: (byte order string like 'big'/'little', struct prefix like '>'/'<')
        """
        if self.is_big_byteorder():
            return 'big', '>'
        else:
            return 'little', '<'

    def unpack(self, fmt_char: str, source: bytes, redefine_byte_order: str = None) -> tuple:
        """
        解包从传感器读取的字节数组。
        Args:
            fmt_char (str): struct 格式字符（c, b, B, h, H, i, I, l, L, q, Q 等）
            source (bytes): 待解包的字节数据
            redefine_byte_order (str, optional): 可选，覆盖默认字节序（如 '<' 或 '>'）

        Returns:
            tuple: 解包后的元组

        Raises:
            ValueError: 当 fmt_char 为空字符串时

        Notes:
            如果 redefine_byte_order 提供，则使用其第一个字符作为字节序前缀。

        ==========================================
        Unpack bytes read from sensor.
        Args:
            fmt_char (str): struct format character (c, b, B, h, H, i, I, l, L, q, Q etc.)
            source (bytes): Byte data to unpack
            redefine_byte_order (str, optional): Optional, override default byte order (e.g., '<' or '>')

        Returns:
            tuple: Unpacked tuple

        Raises:
            ValueError: When fmt_char is empty string

        Notes:
            If redefine_byte_order is provided, its first character is used as the byte order prefix.
        """
        if not fmt_char:
            raise ValueError(f"Invalid length fmt_char parameter: {len(fmt_char)}")
        bo = self._get_byteorder_as_str()[1]
        if redefine_byte_order is not None:
            bo = redefine_byte_order[0]
        return struct.unpack(bo + fmt_char, source)

    @micropython.native
    def is_big_byteorder(self) -> bool:
        """
        返回字节序标志。
        Returns:
            bool: True 表示大端，False 表示小端
        ==========================================
        Return byte order flag.
        Returns:
            bool: True for big-endian, False for little-endian
        """
        return self.big_byte_order


class BaseSensor(Device):
    """
    传感器基类，扩展 Device 并定义标准传感器接口。
    Methods:
        get_id(): 获取传感器 ID（需子类实现）
        soft_reset(): 软件复位传感器（需子类实现）

    Notes:
        子类必须实现 get_id 和 soft_reset 方法。

    ==========================================
    Base sensor class extending Device and defining standard sensor interface.
    Methods:
        get_id(): Get sensor ID (must be implemented by subclass)
        soft_reset(): Software reset of sensor (must be implemented by subclass)

    Notes:
        Subclasses must implement get_id and soft_reset methods.
    """
    def get_id(self) -> int:
        """
        获取传感器 ID。
        Returns:
            int: 传感器标识符

        Raises:
            NotImplementedError: 子类必须重写此方法
        ==========================================
        Get sensor ID.
        Returns:
            int: Sensor identifier

        Raises:
            NotImplementedError: Subclass must override this method
        """
        raise NotImplementedError

    def soft_reset(self) -> None:
        """
        软件复位传感器。
        Raises:
            NotImplementedError: 子类必须重写此方法
        ==========================================
        Perform software reset of sensor.
        Raises:
            NotImplementedError: Subclass must override this method
        """
        raise NotImplementedError


class Iterator:
    """
    迭代器基类，定义 __iter__ 和 __next__ 接口。
    Methods:
        __iter__(): 返回迭代器自身
        __next__(): 获取下一个元素（需子类实现）

    ==========================================
    Base iterator class defining __iter__ and __next__ interface.
    Methods:
        __iter__(): Return iterator itself
        __next__(): Get next element (must be implemented by subclass)
    """
    def __iter__(self):
        """
        返回迭代器自身。
        Returns:
            Iterator: 迭代器实例
        ==========================================
        Return iterator itself.
        Returns:
            Iterator: Iterator instance
        """
        return self

    def __next__(self):
        """
        获取下一个元素。
        Raises:
            NotImplementedError: 子类必须重写此方法
        ==========================================
        Get next element.
        Raises:
            NotImplementedError: Subclass must override this method
        """
        raise NotImplementedError


class TemperatureSensor:
    """
    温度传感器辅助接口，定义温度测量相关方法。
    Methods:
        enable_temp_meas(): 启用/禁用温度测量
        get_temperature(): 获取温度值（摄氏度）

    Notes:
        若传感器不包含温度测量功能，子类可实现为空操作或返回固定值。

    ==========================================
    Auxiliary temperature sensor interface defining temperature measurement methods.
    Methods:
        enable_temp_meas(): Enable/disable temperature measurement
        get_temperature(): Get temperature value (Celsius)

    Notes:
        If sensor does not have temperature measurement, subclass may implement as no-op or return fixed value.
    """
    def enable_temp_meas(self, enable: bool = True) -> None:
        """
        启用或禁用温度测量。
        Args:
            enable (bool): True 启用，False 禁用，默认为 True

        Notes:
            子类可根据实际传感器实现此方法，若不支持可留空。

        ==========================================
        Enable or disable temperature measurement.
        Args:
            enable (bool): True to enable, False to disable, default True

        Notes:
            Subclass may implement according to actual sensor; can be left empty if not supported.
        """
        raise NotImplementedError

    def get_temperature(self) -> [int, float]:
        """
        获取温度值。
        Returns:
            int, float: 温度值（摄氏度）

        Raises:
            NotImplementedError: 子类必须重写此方法

        ==========================================
        Get temperature value.
        Returns:
            int, float: Temperature value in Celsius

        Raises:
            NotImplementedError: Subclass must override this method
        """
        raise NotImplementedError

# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================