# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026-03-23 下午4:00
# @Author  : octaprog7
# @File    : bus_service.py
# @Description : MicroPython I2C/SPI总线适配器模块，提供统一的寄存器读写接口
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# micropython
# MIT license
# Copyright (c) 2022 Roman Shevchik   goctaprog@gmail.com
"""MicroPython модуль для работы с шинами ввода/вывода"""

# ======================================== 导入相关模块 =========================================

import math
from machine import I2C, SPI, Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def _mpy_bl(value: int) -> int:
    """
    计算整数占用的位数（模拟 int.bit_length()）
    Args:
        value (int): 输入整数

    Returns:
        int: 二进制表示的位数，0 返回 0

    Notes:
        MicroPython 标准库缺少 int.bit_length()，本函数实现相同功能。

    ==========================================
    Calculate the number of bits required to represent an integer (simulate int.bit_length())
    Args:
        value (int): Input integer

    Returns:
        int: Number of bits in binary representation, returns 0 for 0

    Notes:
        MicroPython standard library lacks int.bit_length(), this function provides equivalent functionality.
    """
    if 0 == value:
        return 0
    return 1 + int(math.log2(abs(value)))

# ======================================== 自定义类 ============================================

class BusAdapter:
    """
    I2C/SPI 总线适配器基类，定义统一的寄存器读写接口
    Attributes:
        bus (I2C, SPI): 总线对象（I2C 或 SPI 实例）

    Methods:
        get_bus_type(): 返回总线类型
        read_register(): 读取寄存器
        write_register(): 写入寄存器
        read(): 读取原始数据
        write(): 写入原始数据
        write_const(): 重复写入常量值

    Notes:
        子类需实现具体总线协议的读写方法。

    ==========================================
    Base class for I2C/SPI bus adapter, defining unified register read/write interface
    Attributes:
        bus (I2C, SPI): Bus object (I2C or SPI instance)

    Methods:
        get_bus_type(): Return bus type
        read_register(): Read register
        write_register(): Write register
        read(): Read raw data
        write(): Write raw data
        write_const(): Write constant value repeatedly

    Notes:
        Subclasses must implement bus-specific read/write methods.
    """
    def __init__(self, bus: [I2C, SPI]) -> None:
        """
        初始化总线适配器
        Args:
            bus (I2C, SPI): 总线对象

        ==========================================
        Initialize bus adapter
        Args:
            bus (I2C, SPI): Bus object
        """
        self.bus = bus

    def get_bus_type(self) -> type:
        """
        返回总线类型
        Returns:
            type: I2C 或 SPI 的类型对象

        ==========================================
        Return bus type
        Returns:
            type: Type object of I2C or SPI
        """
        return type(self.bus)

    def read_register(self, device_addr: [int, Pin], reg_addr: int, bytes_count: int) -> bytes:
        """
        读取设备寄存器
        Args:
            device_addr (int, Pin): 设备地址（I2C 为整数，SPI 为片选引脚）
            reg_addr (int): 寄存器地址
            bytes_count (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        Raises:
            NotImplementedError: 子类必须实现

        ==========================================
        Read device register
        Args:
            device_addr (int, Pin): Device address (int for I2C, Pin for SPI chip select)
            reg_addr (int): Register address
            bytes_count (int): Number of bytes to read

        Returns:
            bytes: Read data

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    def write_register(self, device_addr: [int, Pin], reg_addr: int, value: [int, bytes, bytearray],
                       bytes_count: int, byte_order: str) -> None:
        """
        写入设备寄存器
        Args:
            device_addr (int, Pin): 设备地址
            reg_addr (int): 寄存器地址
            value (int, bytes, bytearray): 要写入的值
            bytes_count (int): 写入字节数
            byte_order (str): 字节序（'big' 或 'little'）

        Raises:
            NotImplementedError: 子类必须实现

        ==========================================
        Write device register
        Args:
            device_addr (int, Pin): Device address
            reg_addr (int): Register address
            value (int, bytes, bytearray): Value to write
            bytes_count (int): Number of bytes to write
            byte_order (str): Byte order ('big' or 'little')

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    def read(self, device_addr: [int, Pin], n_bytes: int) -> bytes:
        """
        从设备读取原始数据
        Args:
            device_addr (int, Pin): 设备地址
            n_bytes (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        Raises:
            NotImplementedError: 子类必须实现

        ==========================================
        Read raw data from device
        Args:
            device_addr (int, Pin): Device address
            n_bytes (int): Number of bytes to read

        Returns:
            bytes: Read data

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    def write(self, device_addr: [int, Pin], buf: bytes) -> None:
        """
        向设备写入原始数据
        Args:
            device_addr (int, Pin): 设备地址
            buf (bytes): 要写入的数据

        Raises:
            NotImplementedError: 子类必须实现

        ==========================================
        Write raw data to device
        Args:
            device_addr (int, Pin): Device address
            buf (bytes): Data to write

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    def write_const(self, device_addr: [int, Pin], val: int, count: int) -> None:
        """
        重复写入常量值到设备（用于填充屏幕等场景）
        Args:
            device_addr (int, Pin): 设备地址
            val (int): 常量值（0-255）
            count (int): 重复次数

        Raises:
            ValueError: 当 val 超过 8 位时

        Notes:
            此方法对于低速总线效率较低，谨慎使用。

        ==========================================
        Write constant value repeatedly to device (for filling screen, etc.)
        Args:
            device_addr (int, Pin): Device address
            val (int): Constant value (0-255)
            count (int): Number of repetitions

        Raises:
            ValueError: When val exceeds 8 bits

        Notes:
            This method is inefficient for slow buses, use with caution.
        """
        if 0 == count:
            return  # no nothing
        # bl = val.bit_length()     # bit_length() not available in MicroPython
        bl = _mpy_bl(val)
        if bl > 8:
            raise ValueError(f"The value must take no more than 8 bits! Current: {bl}")
        _max = 16
        if count < _max:
            _max = count
        # calculate number of loop iterations
        repeats = count // _max  # number of iterations
        b = bytearray([val for _ in range(_max)])
        for _ in range(repeats):
            self.write(device_addr, b)
        # calculate remainder
        remainder = count - _max * repeats
        if remainder:
            b = bytearray([val for _ in range(remainder)])
            self.write(device_addr, b)


class I2cAdapter(BusAdapter):
    """
    I2C 总线适配器，实现 I2C 协议的寄存器读写
    Methods:
        read_register(): 读取 I2C 寄存器
        write_register(): 写入 I2C 寄存器
        read(): 从 I2C 设备读取数据
        readfrom_into(): 读取到缓冲区
        read_buf_from_mem(): 从内存地址读取到缓冲区
        write(): 向 I2C 设备写入数据
        write_buf_to_mem(): 将缓冲区数据写入内存地址

    ==========================================
    I2C bus adapter implementing I2C protocol register access
    Methods:
        read_register(): Read I2C register
        write_register(): Write I2C register
        read(): Read from I2C device
        readfrom_into(): Read into buffer
        read_buf_from_mem(): Read from memory address into buffer
        write(): Write to I2C device
        write_buf_to_mem(): Write buffer to memory address
    """
    def __init__(self, bus: I2C) -> None:
        """
        初始化 I2C 适配器
        Args:
            bus (I2C): I2C 总线对象

        ==========================================
        Initialize I2C adapter
        Args:
            bus (I2C): I2C bus object
        """
        super().__init__(bus)

    def write_register(self, device_addr: int, reg_addr: int, value: [int, bytes, bytearray],
                       bytes_count: int, byte_order: str) -> None:
        """
        写入 I2C 寄存器
        Args:
            device_addr (int): I2C 设备地址
            reg_addr (int): 寄存器地址
            value (int, bytes, bytearray): 要写入的值
            bytes_count (int): 写入字节数
            byte_order (str): 字节序

        ==========================================
        Write I2C register
        Args:
            device_addr (int): I2C device address
            reg_addr (int): Register address
            value (int, bytes, bytearray): Value to write
            bytes_count (int): Number of bytes to write
            byte_order (str): Byte order
        """
        buf = None
        if isinstance(value, int):
            buf = value.to_bytes(bytes_count, byte_order)
        if isinstance(value, (bytes, bytearray)):
            buf = value

        return self.bus.writeto_mem(device_addr, reg_addr, buf)

    def read_register(self, device_addr: int, reg_addr: int, bytes_count: int) -> bytes:
        """
        读取 I2C 寄存器
        Args:
            device_addr (int): I2C 设备地址
            reg_addr (int): 寄存器地址
            bytes_count (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        ==========================================
        Read I2C register
        Args:
            device_addr (int): I2C device address
            reg_addr (int): Register address
            bytes_count (int): Number of bytes to read

        Returns:
            bytes: Read data
        """
        return self.bus.readfrom_mem(device_addr, reg_addr, bytes_count)

    def read(self, device_addr: int, n_bytes: int) -> bytes:
        """
        从 I2C 设备读取原始数据
        Args:
            device_addr (int): I2C 设备地址
            n_bytes (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        ==========================================
        Read raw data from I2C device
        Args:
            device_addr (int): I2C device address
            n_bytes (int): Number of bytes to read

        Returns:
            bytes: Read data
        """
        return self.bus.readfrom(device_addr, n_bytes)

    def readfrom_into(self, device_addr: int, buf) -> None:
        """
        从 I2C 设备读取数据到缓冲区
        Args:
            device_addr (int): I2C 设备地址
            buf: 缓冲区，长度决定读取字节数

        ==========================================
        Read data from I2C device into buffer
        Args:
            device_addr (int): I2C device address
            buf: Buffer, its length determines number of bytes to read
        """
        return self.bus.readfrom_into(device_addr, buf)

    def read_buf_from_mem(self, device_addr: int, mem_addr, buf) -> None:
        """
        从 I2C 设备内存地址读取数据到缓冲区
        Args:
            device_addr (int): I2C 设备地址
            mem_addr: 内存地址
            buf: 缓冲区，长度决定读取字节数

        ==========================================
        Read data from I2C device memory address into buffer
        Args:
            device_addr (int): I2C device address
            mem_addr: Memory address
            buf: Buffer, its length determines number of bytes to read
        """
        return self.bus.readfrom_mem_into(device_addr, mem_addr, buf)

    def write(self, device_addr: int, buf: bytes) -> None:
        """
        向 I2C 设备写入数据
        Args:
            device_addr (int): I2C 设备地址
            buf (bytes): 要写入的数据

        ==========================================
        Write data to I2C device
        Args:
            device_addr (int): I2C device address
            buf (bytes): Data to write
        """
        return self.bus.writeto(device_addr, buf)

    def write_buf_to_mem(self, device_addr: int, mem_addr, buf) -> None:
        """
        将缓冲区数据写入 I2C 设备内存地址
        Args:
            device_addr (int): I2C 设备地址
            mem_addr: 内存地址
            buf: 要写入的数据缓冲区

        ==========================================
        Write buffer data to I2C device memory address
        Args:
            device_addr (int): I2C device address
            mem_addr: Memory address
            buf: Data buffer to write
        """
        return self.bus.writeto_mem(device_addr, mem_addr, buf)


class SpiAdapter(BusAdapter):
    """
    SPI 总线适配器，支持数据/命令模式引脚
    Attributes:
        _data_mode_pin (Pin, optional): 数据/命令模式控制引脚
        _use_data_mode_pin (bool): 是否使用数据模式引脚
        _data_packet (bool): 当前传输是否为数据包

    Methods:
        read(): 从 SPI 设备读取数据
        readinto(): 读取数据到缓冲区
        write(): 写入数据到 SPI 设备
        write_and_read(): 同时写入和读取
        use_data_mode_pin: 属性，获取是否使用数据模式引脚
        data_mode_pin: 属性，获取数据模式引脚对象

    Notes:
        SPI 设备通常通过片选引脚（device_addr）选择，并支持数据/命令模式切换。

    ==========================================
    SPI bus adapter with support for data/command mode pin
    Attributes:
        _data_mode_pin (Pin, optional): Data/command mode control pin
        _use_data_mode_pin (bool): Whether to use data mode pin
        _data_packet (bool): Whether current transfer is a data packet

    Methods:
        read(): Read data from SPI device
        readinto(): Read data into buffer
        write(): Write data to SPI device
        write_and_read(): Simultaneous write and read
        use_data_mode_pin: Property to check if data mode pin is used
        data_mode_pin: Property to get data mode pin object

    Notes:
        SPI devices are selected via chip select pin (device_addr) and may support data/command mode switching.
    """
    def __init__(self, bus: SPI, data_mode: Pin = None) -> None:
        """
        初始化 SPI 适配器
        Args:
            bus (SPI): SPI 总线对象
            data_mode (Pin, optional): 数据模式控制引脚，高电平表示数据，低电平表示命令

        ==========================================
        Initialize SPI adapter
        Args:
            bus (SPI): SPI bus object
            data_mode (Pin, optional): Data mode control pin, high for data, low for command
        """
        super().__init__(bus)
        # MCU pin for data mode
        self._data_mode_pin = data_mode
        # whether to use data mode pin (True) or command mode (False)
        self._use_data_mode_pin = False
        # flag for write methods. If True, data_mode pin will be set to True, otherwise False
        self._data_packet = False

    def read_register(self, device_addr: Pin, reg_addr: int, bytes_count: int) -> bytes:
        """
        SPI 寄存器读取（未实现）
        Raises:
            NotImplementedError: 此方法在 SPI 适配器中未实现

        ==========================================
        SPI register read (not implemented)
        Raises:
            NotImplementedError: This method is not implemented in SPI adapter
        """
        raise NotImplementedError

    def write_register(self, device_addr: Pin, reg_addr: int, value: [int, bytes, bytearray],
                       bytes_count: int, byte_order: str) -> None:
        """
        SPI 寄存器写入（未实现）
        Raises:
            NotImplementedError: 此方法在 SPI 适配器中未实现

        ==========================================
        SPI register write (not implemented)
        Raises:
            NotImplementedError: This method is not implemented in SPI adapter
        """
        raise NotImplementedError

    def read(self, device_addr: Pin, n_bytes: int) -> bytes:
        """
        从 SPI 设备读取数据
        Args:
            device_addr (Pin): 片选引脚对象
            n_bytes (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        Notes:
            读取时连续发送 0x00，并返回读取的字节。

        ==========================================
        Read data from SPI device
        Args:
            device_addr (Pin): Chip select pin object
            n_bytes (int): Number of bytes to read

        Returns:
            bytes: Read data

        Notes:
            Continuously sends 0x00 while reading, returns read bytes.
        """
        try:
            device_addr.low()
            return self.bus.read(n_bytes)
        finally:
            device_addr.high()

    def readinto(self, device_addr: Pin, buf) -> None:
        """
        读取数据到缓冲区
        Args:
            device_addr (Pin): 片选引脚对象
            buf: 缓冲区，长度决定读取字节数

        ==========================================
        Read data into buffer
        Args:
            device_addr (Pin): Chip select pin object
            buf: Buffer, its length determines number of bytes to read
        """
        try:
            device_addr.low()
            return self.bus.readinto(buf, 0x00)
        finally:
            device_addr.high()

    def _manage_dmp(self) -> None:
        """
        管理数据模式引脚状态
        Notes:
            如果启用了数据模式引脚，根据 _data_packet 标志设置引脚电平。

        ==========================================
        Manage data mode pin state
        Notes:
            If data mode pin is enabled, set its level according to _data_packet flag.
        """
        if self._use_data_mode_pin and self._data_mode_pin:
            self._data_mode_pin.value(self._data_packet)

    def write(self, device_addr: Pin, buf: bytes) -> None:
        """
        向 SPI 设备写入数据
        Args:
            device_addr (Pin): 片选引脚对象
            buf (bytes): 要写入的数据

        Notes:
            如果设置了数据模式引脚，写入前会设置该引脚状态。

        ==========================================
        Write data to SPI device
        Args:
            device_addr (Pin): Chip select pin object
            buf (bytes): Data to write

        Notes:
            If data mode pin is configured, its state is set before writing.
        """
        try:
            device_addr.low()
            self._manage_dmp()
            return self.bus.write(buf)
        finally:
            device_addr.high()

    def write_and_read(self, device_addr: Pin, wr_buf: bytes, rd_buf: bytes) -> None:
        """
        同时向 SPI 设备写入和读取数据
        Args:
            device_addr (Pin): 片选引脚对象
            wr_buf (bytes): 要写入的缓冲区
            rd_buf (bytes): 读取数据的缓冲区

        Notes:
            两个缓冲区长度必须相同，写入数据的同时读取数据。

        ==========================================
        Simultaneously write to and read from SPI device
        Args:
            device_addr (Pin): Chip select pin object
            wr_buf (bytes): Write buffer
            rd_buf (bytes): Read buffer

        Notes:
            Both buffers must have the same length; data is written while reading.
        """
        try:
            device_addr.low()
            self._manage_dmp()
            return self.bus.write_readinto(wr_buf, rd_buf)
        finally:
            device_addr.high()

    @property
    def use_data_mode_pin(self) -> bool:
        """
        获取是否使用数据模式引脚
        Returns:
            bool: True 表示启用，False 表示禁用
        ==========================================
        Get whether data mode pin is used
        Returns:
            bool: True if enabled, False if disabled
        """
        return self._use_data_mode_pin

    @property
    def data_mode_pin(self) -> Pin:
        """
        获取数据模式引脚对象
        Returns:
            Pin: 数据模式引脚
        ==========================================
        Get data mode pin object
        Returns:
            Pin: Data mode pin
        """
        return self._data_mode_pin

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================