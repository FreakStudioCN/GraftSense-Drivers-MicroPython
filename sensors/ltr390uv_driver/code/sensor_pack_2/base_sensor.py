# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Roman Shevchik
# @File    : base_sensor.py
# @Description : 传感器驱动基础模块，提供I2C/SPI总线抽象、寄存器访问、类型检查等通用功能
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import struct
import micropython
from sensor_pack_2 import bus_service
from machine import Pin


# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================
@micropython.native
def check_value(value: int | None, valid_range, error_msg: str) -> int | None:
    """
    检查值是否在有效范围内，如果值为None则直接返回
    Args:
        value (int | None): 待检查的值
        valid_range: 有效范围（如range对象）
        error_msg (str): 错误消息

    Returns:
        int | None: 原值或None

    Raises:
        ValueError: 当value不为None且不在valid_range内时

    Notes:
        如果value为None，函数直接返回None而不进行范围检查

    ==========================================
    Check if value is within valid range, return directly if value is None
    Args:
        value (int | None): Value to check
        valid_range: Valid range (e.g. range object)
        error_msg (str): Error message

    Returns:
        int | None: Original value or None

    Raises:
        ValueError: When value is not None and not in valid_range

    Notes:
        If value is None, the function returns None without range check
    """
    if value is None:
        return value
    if value not in valid_range:
        raise ValueError(error_msg)
    return value


def get_error_str(val_name: str, val: int, rng: range) -> str:
    """
    生成详细的错误消息字符串
    Args:
        val_name (str): 变量名
        val (int): 变量值
        rng (range): 有效范围

    Returns:
        str: 格式化的错误消息（英文）

    Notes:
        用于在值超出范围时提供清晰的错误信息

    ==========================================
    Generate detailed error message string
    Args:
        val_name (str): Variable name
        val (int): Variable value
        rng (range): Valid range

    Returns:
        str: Formatted error message (English)

    Notes:
        Used to provide clear error information when value is out of range
    """
    return f"Value {val} of parameter {val_name} is out of range [{rng.start}..{rng.stop - 1}]!"


def all_none(*args) -> bool:
    """
    检查所有传入参数是否均为None
    Args:
        *args: 任意数量的参数

    Returns:
        bool: 如果所有参数都是None则返回True，否则返回False

    Notes:
        添加于2024-01-25

    ==========================================
    Check if all passed arguments are None
    Args:
        *args: Any number of arguments

    Returns:
        bool: True if all arguments are None, otherwise False

    Notes:
        Added on 2024-01-25
    """
    for element in args:
        if element is not None:
            return False
    return True


# ======================================== 自定义类 ============================================
class Device:
    """
    传感器基础类，提供总线适配器和字节序管理
    Attributes:
        adapter (bus_service.BusAdapter): 总线适配器对象
        address (int | Pin): 设备地址或引脚
        big_byte_order (bool): 大端字节序标志
        msb_first (bool): SPI传输时MSB优先标志

    Methods:
        _get_byteorder_as_str(): 获取字节序字符串
        pack(): 打包数据为字节串
        unpack(): 解包字节串为数据
        is_big_byteorder(): 检查是否为大端字节序

    Notes:
        支持I2C和SPI总线，子类应实现具体的传感器功能

    ==========================================
    Base class for sensors, providing bus adapter and byte order management
    Attributes:
        adapter (bus_service.BusAdapter): Bus adapter object
        address (int | Pin): Device address or pin
        big_byte_order (bool): Big-endian flag
        msb_first (bool): MSB first flag for SPI transfer

    Methods:
        _get_byteorder_as_str(): Get byte order as string
        pack(): Pack data into bytes
        unpack(): Unpack bytes into data
        is_big_byteorder(): Check if big-endian

    Notes:
        Supports I2C and SPI buses, subclasses should implement specific sensor functions
    """

    def __init__(self, adapter: bus_service.BusAdapter, address: int | Pin, big_byte_order: bool):
        """
        初始化Device实例
        Args:
            adapter (bus_service.BusAdapter): 总线适配器对象
            address (int | Pin): I2C地址或SPI引脚
            big_byte_order (bool): True表示寄存器值使用大端字节序，False表示小端字节序

        Raises:
            TypeError: 当adapter或address为None时

        Notes:
            如果address为Pin类型，通常用于SPI片选

        ==========================================
        Initialize Device instance
        Args:
            adapter (bus_service.BusAdapter): Bus adapter object
            address (int | Pin): I2C address or SPI pin
            big_byte_order (bool): True for big-endian register values, False for little-endian

        Raises:
            TypeError: When adapter or address is None

        Notes:
            If address is Pin type, it is typically used for SPI chip select
        """
        if adapter is None:
            raise TypeError("adapter cannot be None")
        if address is None:
            raise TypeError("address cannot be None")
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
        以字符串形式返回字节序
        Args:
            无

        Returns:
            tuple: (字节序字符串, struct格式字符) 例如('big', '>')或('little', '<')

        Notes:
            内部方法，供pack/unpack使用

        ==========================================
        Return byte order as string
        Args:
            None

        Returns:
            tuple: (byte order string, struct format character) e.g. ('big', '>') or ('little', '<')

        Notes:
            Internal method for pack/unpack
        """
        if self.is_big_byteorder():
            return "big", ">"
        return "little", "<"

    def pack(self, fmt_char: str, *values) -> bytes:
        """
        将数据打包为字节串
        Args:
            fmt_char (str): struct格式字符（如'B','H'等）
            *values: 要打包的值

        Returns:
            bytes: 打包后的字节串

        Raises:
            ValueError: 当fmt_char为空字符串时

        Notes:
            使用设备字节序进行打包

        ==========================================
        Pack data into bytes
        Args:
            fmt_char (str): struct format character (e.g. 'B','H')
            *values: Values to pack

        Returns:
            bytes: Packed bytes

        Raises:
            ValueError: When fmt_char is empty

        Notes:
            Uses device byte order for packing
        """
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        return struct.pack(bo + fmt_char, *values)

    def unpack(self, fmt_char: str, source: bytes, redefine_byte_order: str = None) -> tuple:
        """
        从字节串解包数据
        Args:
            fmt_char (str): struct格式字符
            source (bytes): 源字节串
            redefine_byte_order (str | None): 重新定义的字节序（可选）

        Returns:
            tuple: 解包后的数据元组

        Raises:
            ValueError: 当fmt_char为空字符串时

        Notes:
            如果提供redefine_byte_order，则使用其第一个字符作为字节序

        ==========================================
        Unpack data from bytes
        Args:
            fmt_char (str): struct format character
            source (bytes): Source bytes
            redefine_byte_order (str | None): Redefined byte order (optional)

        Returns:
            tuple: Unpacked data tuple

        Raises:
            ValueError: When fmt_char is empty

        Notes:
            If redefine_byte_order is provided, its first character is used as byte order
        """
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        if redefine_byte_order is not None:
            bo = redefine_byte_order[0]
        return struct.unpack(bo + fmt_char, source)

    @micropython.native
    def is_big_byteorder(self) -> bool:
        """
        检查是否为大端字节序
        Args:
            无

        Returns:
            bool: True表示大端字节序，False表示小端字节序

        ==========================================
        Check if big-endian
        Args:
            None

        Returns:
            bool: True for big-endian, False for little-endian
        """
        return self.big_byte_order


class DeviceEx(Device):
    """
    扩展的设备类，添加了通用的总线读写方法
    Attributes:
        继承自Device的所有属性

    Methods:
        read_reg(): 读取寄存器
        write_reg(): 写寄存器
        read(): 从设备读取指定字节数
        read_to_buf(): 读取到缓冲区
        write(): 写入字节数据
        read_buf_from_mem(): 从内存地址读取到缓冲区
        write_buf_to_mem(): 将缓冲区写入内存地址

    Notes:
        提供便捷的I2C/SPI操作，子类无需重复实现

    ==========================================
    Extended device class adding common bus read/write methods
    Attributes:
        Inherits all attributes from Device

    Methods:
        read_reg(): Read register
        write_reg(): Write register
        read(): Read specified number of bytes from device
        read_to_buf(): Read into buffer
        write(): Write bytes data
        read_buf_from_mem(): Read from memory address into buffer
        write_buf_to_mem(): Write buffer to memory address

    Notes:
        Provides convenient I2C/SPI operations, subclasses need not re-implement
    """

    def read_reg(self, reg_addr: int, bytes_count: int = 2) -> bytes:
        """
        从指定寄存器读取数据
        Args:
            reg_addr (int): 寄存器地址
            bytes_count (int): 要读取的字节数，默认为2

        Returns:
            bytes: 读取到的字节数据

        Raises:
            TypeError: 当reg_addr为None时

        Notes:
            依赖底层总线适配器的read_register方法

        ==========================================
        Read data from specified register
        Args:
            reg_addr (int): Register address
            bytes_count (int): Number of bytes to read, default 2

        Returns:
            bytes: Read bytes data

        Raises:
            TypeError: When reg_addr is None

        Notes:
            Relies on the bus adapter's read_register method
        """
        if reg_addr is None:
            raise TypeError("reg_addr cannot be None")
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def write_reg(self, reg_addr: int, value: int | bytes | bytearray, bytes_count: int) -> int:
        """
        向指定寄存器写入数据
        Args:
            reg_addr (int): 寄存器地址
            value (int | bytes | bytearray): 要写入的值
            bytes_count (int): 写入的字节数

        Returns:
            int: 实际写入的字节数

        Raises:
            TypeError: 当reg_addr或value为None时

        Notes:
            自动处理字节序

        ==========================================
        Write data to specified register
        Args:
            reg_addr (int): Register address
            value (int | bytes | bytearray): Value to write
            bytes_count (int): Number of bytes to write

        Returns:
            int: Number of bytes actually written

        Raises:
            TypeError: When reg_addr or value is None

        Notes:
            Handles byte order automatically
        """
        if reg_addr is None:
            raise TypeError("reg_addr cannot be None")
        if value is None:
            raise TypeError("value cannot be None")
        byte_order = self._get_byteorder_as_str()[0]
        return self.adapter.write_register(self.address, reg_addr, value, bytes_count, byte_order)

    def read(self, n_bytes: int) -> bytes:
        """
        从设备读取指定字节数
        Args:
            n_bytes (int): 要读取的字节数

        Returns:
            bytes: 读取到的字节数据

        Raises:
            TypeError: 当n_bytes为None时

        Notes:
            无

        ==========================================
        Read specified number of bytes from device
        Args:
            n_bytes (int): Number of bytes to read

        Returns:
            bytes: Read bytes data

        Raises:
            TypeError: When n_bytes is None

        Notes:
            None
        """
        if n_bytes is None:
            raise TypeError("n_bytes cannot be None")
        return self.adapter.read(self.address, n_bytes)

    def read_to_buf(self, buf) -> bytes:
        """
        将设备数据读取到缓冲区
        Args:
            buf: 缓冲区对象（需支持写入）

        Returns:
            bytes: 读取的字节数据

        Raises:
            TypeError: 当buf为None时

        Notes:
            缓冲区长度决定了读取的字节数

        ==========================================
        Read device data into buffer
        Args:
            buf: Buffer object (must support writing)

        Returns:
            bytes: Read bytes data

        Raises:
            TypeError: When buf is None

        Notes:
            Buffer length determines number of bytes to read
        """
        if buf is None:
            raise TypeError("buf cannot be None")
        return self.adapter.read_to_buf(self.address, buf)

    def write(self, buf: bytes):
        """
        向设备写入字节数据
        Args:
            buf (bytes): 要写入的字节数据

        Raises:
            TypeError: 当buf为None时

        Notes:
            无

        ==========================================
        Write bytes data to device
        Args:
            buf (bytes): Bytes data to write

        Raises:
            TypeError: When buf is None

        Notes:
            None
        """
        if buf is None:
            raise TypeError("buf cannot be None")
        return self.adapter.write(self.address, buf)

    def read_buf_from_mem(self, address: int, buf, address_size: int = 1):
        """
        从设备内存地址读取数据到缓冲区
        Args:
            address (int): 起始内存地址
            buf: 缓冲区对象
            address_size (int): 地址字节数，默认为1

        Raises:
            TypeError: 当address或buf为None时

        Notes:
            读取字节数等于缓冲区长度

        ==========================================
        Read data from device memory address into buffer
        Args:
            address (int): Starting memory address
            buf: Buffer object
            address_size (int): Number of address bytes, default 1

        Raises:
            TypeError: When address or buf is None

        Notes:
            Number of bytes read equals buffer length
        """
        if address is None:
            raise TypeError("address cannot be None")
        if buf is None:
            raise TypeError("buf cannot be None")
        return self.adapter.read_buf_from_memory(self.address, address, buf, address_size)

    def write_buf_to_mem(self, mem_addr, buf):
        """
        将缓冲区数据写入设备内存
        Args:
            mem_addr: 目标内存地址
            buf: 缓冲区对象

        Raises:
            TypeError: 当mem_addr或buf为None时

        Notes:
            写入字节数等于缓冲区长度

        ==========================================
        Write buffer data to device memory
        Args:
            mem_addr: Target memory address
            buf: Buffer object

        Raises:
            TypeError: When mem_addr or buf is None

        Notes:
            Number of bytes written equals buffer length
        """
        if mem_addr is None:
            raise TypeError("mem_addr cannot be None")
        if buf is None:
            raise TypeError("buf cannot be None")
        return self.adapter.write_buf_to_memory(self.address, mem_addr, buf)


class BaseSensor(Device):
    """
    传感器基类，定义了基本传感器接口
    Methods:
        get_id(): 获取设备ID
        soft_reset(): 软件复位

    Notes:
        抽象基类，子类必须实现get_id和soft_reset方法

    ==========================================
    Base class for sensors, defines basic sensor interface
    Methods:
        get_id(): Get device ID
        soft_reset(): Software reset

    Notes:
        Abstract base class, subclasses must implement get_id and soft_reset
    """

    def get_id(self):
        """获取设备ID，子类必须实现"""
        raise NotImplementedError

    def soft_reset(self):
        """软件复位，子类必须实现"""
        raise NotImplementedError


class BaseSensorEx(DeviceEx):
    """
    扩展传感器基类，继承自DeviceEx
    Methods:
        get_id(): 获取设备ID
        soft_reset(): 软件复位

    Notes:
        抽象基类，子类必须实现get_id和soft_reset方法

    ==========================================
    Extended sensor base class, inherits from DeviceEx
    Methods:
        get_id(): Get device ID
        soft_reset(): Software reset

    Notes:
        Abstract base class, subclasses must implement get_id and soft_reset
    """

    def get_id(self):
        """获取设备ID，子类必须实现"""
        raise NotImplementedError

    def soft_reset(self):
        """软件复位，子类必须实现"""
        raise NotImplementedError


class Iterator:
    """
    迭代器协议基类
    Methods:
        __iter__(): 返回迭代器自身
        __next__(): 获取下一个值，子类必须实现

    Notes:
        配合传感器数据读取使用

    ==========================================
    Iterator protocol base class
    Methods:
        __iter__(): Return iterator itself
        __next__(): Get next value, must be implemented by subclass

    Notes:
        Used with sensor data reading
    """

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError


class TemperatureSensor:
    """
    温度传感器辅助类
    Methods:
        enable_temp_meas(): 使能温度测量
        get_temperature(): 获取温度值

    Notes:
        作为主传感器或辅助温度传感器，子类应重写方法

    ==========================================
    Temperature sensor helper class
    Methods:
        enable_temp_meas(): Enable temperature measurement
        get_temperature(): Get temperature value

    Notes:
        Can be used as primary or auxiliary temperature sensor, subclasses should override methods
    """

    def enable_temp_meas(self, enable: bool = True):
        """
        使能温度测量
        Args:
            enable (bool): True表示使能，False表示禁能

        Notes:
            子类应重写此方法

        ==========================================
        Enable temperature measurement
        Args:
            enable (bool): True to enable, False to disable

        Notes:
            Subclasses should override this method
        """
        raise NotImplementedError

    def get_temperature(self) -> int | float:
        """
        获取温度值
        Returns:
            int | float: 温度值（摄氏度）

        Notes:
            子类应重写此方法

        ==========================================
        Get temperature value
        Returns:
            int | float: Temperature in degrees Celsius

        Notes:
            Subclasses should override this method
        """
        raise NotImplementedError


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
