# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2022/01/01 00:00
# @Author  : Roman Shevchik (goctaprog@gmail.com)
# @File    : base_sensor.py
# @Description : MicroPython传感器基类，提供Device/DeviceEx/BaseSensor/Iterator/TemperatureSensor基础抽象
# @License : MIT

__version__ = "1.0.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import struct
import micropython
from sensor_pack_2 import bus_service
from machine import Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


@micropython.native
def check_value(value, valid_range, error_msg: str):
    """
    校验值是否在合法范围内（None值直接通过）
    Args:
        value: 待校验值，None时直接返回
        valid_range: 合法范围（支持range或容器）
        error_msg (str): 超出范围时的错误信息
    Returns:
        原始值（通过校验）或None
    Raises:
        ValueError: value不在valid_range中
    Notes:
        - ISR-safe: 是
    ==========================================
    Validate value is within valid range (None passes directly).
    Args:
        value: Value to validate, returns directly if None
        valid_range: Valid range (supports range or container)
        error_msg (str): Error message if out of range
    Returns:
        Original value if valid, or None
    Raises:
        ValueError: value not in valid_range
    Notes:
        - ISR-safe: Yes
    """
    if value is None:
        return value
    if value not in valid_range:
        raise ValueError(error_msg)
    return value


def all_none(*args) -> bool:
    """
    判断所有输入参数是否均为None
    Args:
        *args: 任意数量的参数
    Returns:
        bool: 所有参数均为None时返回True，否则返回False
    Notes:
        - ISR-safe: 是
    ==========================================
    Check if all input arguments are None.
    Args:
        *args: Any number of arguments
    Returns:
        bool: True if all arguments are None, False otherwise
    Notes:
        - ISR-safe: Yes
    """
    for element in args:
        if element is not None:
            return False
    return True


# ======================================== 自定义类 ============================================


class Device:
    """
    设备基类，封装总线适配器和字节序配置
    Attributes:
        adapter (BusAdapter): 总线适配器实例
        address: 设备总线地址（I2C为int，SPI为Pin）
        big_byte_order (bool): True=大端字节序，False=小端字节序
        msb_first (bool): SPI传输时最高位优先标志
    Methods:
        _get_byteorder_as_str(): 返回字节序字符串表示
        pack(): 按设备字节序打包数据
        unpack(): 按设备字节序解包数据
        is_big_byteorder(): 返回是否大端字节序
    Notes:
        - 依赖外部传入总线适配器实例
    ==========================================
    Base device class encapsulating bus adapter and byte order config.
    Attributes:
        adapter (BusAdapter): Bus adapter instance
        address: Device bus address (int for I2C, Pin for SPI)
        big_byte_order (bool): True=big endian, False=little endian
        msb_first (bool): SPI MSB-first flag
    Methods:
        _get_byteorder_as_str(): Return byte order as string
        pack(): Pack data with device byte order
        unpack(): Unpack data with device byte order
        is_big_byteorder(): Return whether big endian
    Notes:
        - Requires externally provided bus adapter instance
    """

    def __init__(self, adapter: bus_service.BusAdapter, address, big_byte_order: bool):
        """
        初始化设备基类
        Args:
            adapter (BusAdapter): 总线适配器实例
            address: 设备总线地址（I2C为int，SPI为Pin）
            big_byte_order (bool): True=大端字节序，False=小端字节序
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize base device.
        Args:
            adapter (BusAdapter): Bus adapter instance
            address: Device bus address (int for I2C, Pin for SPI)
            big_byte_order (bool): True=big endian, False=little endian
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        self.adapter = adapter
        self.address = address
        self.big_byte_order = big_byte_order
        self.msb_first = True

    def _get_byteorder_as_str(self) -> tuple:
        """
        返回字节序的字符串表示
        Returns:
            tuple: ('big','>')或('little','<')
        Notes:
            - ISR-safe: 是
        ==========================================
        Return byte order as string tuple.
        Returns:
            tuple: ('big','>') or ('little','<')
        Notes:
            - ISR-safe: Yes
        """
        if self.is_big_byteorder():
            return 'big', '>'
        return 'little', '<'

    def pack(self, fmt_char: str, *values) -> bytes:
        """
        按设备字节序打包数据
        Args:
            fmt_char (str): struct格式字符
            *values: 待打包数值
        Returns:
            bytes: 打包后的字节数据
        Raises:
            ValueError: fmt_char为空
        Notes:
            - ISR-safe: 否
        ==========================================
        Pack data with device byte order.
        Args:
            fmt_char (str): struct format character
            *values: Values to pack
        Returns:
            bytes: Packed byte data
        Raises:
            ValueError: fmt_char is empty
        Notes:
            - ISR-safe: No
        """
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        return struct.pack(bo + fmt_char, values)

    def unpack(self, fmt_char: str, source: bytes, redefine_byte_order: str = None) -> tuple:
        """
        按设备字节序解包字节数据
        Args:
            fmt_char (str): struct格式字符
            source (bytes): 待解包字节数据
            redefine_byte_order (str): 覆盖默认字节序，None则使用设备配置
        Returns:
            tuple: 解包后的数值元组
        Raises:
            ValueError: fmt_char为空
        Notes:
            - ISR-safe: 否
        ==========================================
        Unpack byte data with device byte order.
        Args:
            fmt_char (str): struct format character
            source (bytes): Bytes to unpack
            redefine_byte_order (str): Override default byte order, None uses device config
        Returns:
            tuple: Unpacked value tuple
        Raises:
            ValueError: fmt_char is empty
        Notes:
            - ISR-safe: No
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
        返回是否使用大端字节序
        Returns:
            bool: True=大端，False=小端
        Notes:
            - ISR-safe: 是
        ==========================================
        Return whether big endian byte order is used.
        Returns:
            bool: True=big endian, False=little endian
        Notes:
            - ISR-safe: Yes
        """
        return self.big_byte_order


class DeviceEx(Device):
    """
    扩展设备基类，封装通用寄存器读写方法
    Methods:
        read_reg(): 读取寄存器值
        write_reg(): 写入寄存器值
        read(): 从设备读取字节
        read_to_buf(): 读取到缓冲区
        write(): 向设备写入字节
        read_buf_from_mem(): 从内存地址读取到缓冲区
        write_buf_to_mem(): 将缓冲区写入内存地址
    ==========================================
    Extended device base class with common register read/write methods.
    Methods:
        read_reg(): Read register value
        write_reg(): Write register value
        read(): Read bytes from device
        read_to_buf(): Read into buffer
        write(): Write bytes to device
        read_buf_from_mem(): Read from memory address into buffer
        write_buf_to_mem(): Write buffer to memory address
    """

    def read_reg(self, reg_addr: int, bytes_count=2) -> bytes:
        """
        从设备寄存器读取值
        Args:
            reg_addr (int): 寄存器地址
            bytes_count (int): 读取字节数，默认2
        Returns:
            bytes: 读取到的字节数据
        Notes:
            - ISR-safe: 否
        ==========================================
        Read value from device register.
        Args:
            reg_addr (int): Register address
            bytes_count (int): Number of bytes to read, default 2
        Returns:
            bytes: Read byte data
        Notes:
            - ISR-safe: No
        """
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def write_reg(self, reg_addr: int, value, bytes_count) -> int:
        """
        向设备寄存器写入值
        Args:
            reg_addr (int): 寄存器地址
            value: 写入值（int/bytes/bytearray）
            bytes_count (int): 写入字节数
        Returns:
            int: 写入结果
        Notes:
            - ISR-safe: 否
        ==========================================
        Write value to device register.
        Args:
            reg_addr (int): Register address
            value: Value to write (int/bytes/bytearray)
            bytes_count (int): Number of bytes to write
        Returns:
            int: Write result
        Notes:
            - ISR-safe: No
        """
        byte_order = self._get_byteorder_as_str()[0]
        return self.adapter.write_register(self.address, reg_addr, value, bytes_count, byte_order)

    def read(self, n_bytes: int) -> bytes:
        """
        从设备读取指定字节数
        Args:
            n_bytes (int): 读取字节数
        Returns:
            bytes: 读取到的字节数据
        Notes:
            - ISR-safe: 否
        ==========================================
        Read specified bytes from device.
        Args:
            n_bytes (int): Number of bytes to read
        Returns:
            bytes: Read byte data
        Notes:
            - ISR-safe: No
        """
        return self.adapter.read(self.address, n_bytes)

    def read_to_buf(self, buf) -> bytes:
        """
        从设备读取数据到缓冲区
        Args:
            buf (bytearray): 目标缓冲区
        Returns:
            bytes: 缓冲区引用
        Notes:
            - ISR-safe: 否
        ==========================================
        Read data from device into buffer.
        Args:
            buf (bytearray): Target buffer
        Returns:
            bytes: Buffer reference
        Notes:
            - ISR-safe: No
        """
        return self.adapter.read_to_buf(self.address, buf)

    def write(self, buf: bytes):
        """
        向设备写入字节数据
        Args:
            buf (bytes): 待写入字节数据
        Notes:
            - ISR-safe: 否
        ==========================================
        Write byte data to device.
        Args:
            buf (bytes): Byte data to write
        Notes:
            - ISR-safe: No
        """
        return self.adapter.write(self.address, buf)

    def read_buf_from_mem(self, address: int, buf, address_size: int = 1):
        """
        从设备内存地址读取数据到缓冲区
        Args:
            address (int): 设备内存起始地址
            buf (bytearray): 目标缓冲区
            address_size (int): 地址字节数，默认1
        Notes:
            - ISR-safe: 否
        ==========================================
        Read data from device memory address into buffer.
        Args:
            address (int): Device memory start address
            buf (bytearray): Target buffer
            address_size (int): Address size in bytes, default 1
        Notes:
            - ISR-safe: No
        """
        return self.adapter.read_buf_from_memory(self.address, address, buf, address_size)

    def write_buf_to_mem(self, mem_addr, buf):
        """
        将缓冲区数据写入设备内存地址
        Args:
            mem_addr: 设备内存起始地址
            buf (bytearray): 待写入缓冲区
        Notes:
            - ISR-safe: 否
        ==========================================
        Write buffer data to device memory address.
        Args:
            mem_addr: Device memory start address
            buf (bytearray): Buffer to write
        Notes:
            - ISR-safe: No
        """
        return self.adapter.write_buf_to_memory(self.address, mem_addr, buf)


class BaseSensor(Device):
    """
    传感器基类（继承Device），定义传感器通用接口
    Methods:
        get_id(): 读取芯片ID（子类实现）
        soft_reset(): 软件复位（子类实现）
    ==========================================
    Base sensor class (extends Device), defines common sensor interface.
    Methods:
        get_id(): Read chip ID (subclass implements)
        soft_reset(): Software reset (subclass implements)
    """

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class BaseSensorEx(DeviceEx):
    """
    扩展传感器基类（继承DeviceEx），定义传感器通用接口
    Methods:
        get_id(): 读取芯片ID（子类实现）
        soft_reset(): 软件复位（子类实现）
    ==========================================
    Extended base sensor class (extends DeviceEx), defines common sensor interface.
    Methods:
        get_id(): Read chip ID (subclass implements)
        soft_reset(): Software reset (subclass implements)
    """

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class Iterator:
    """
    迭代器混入类，为传感器提供迭代接口
    ==========================================
    Iterator mixin class providing iteration interface for sensors.
    """

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError


class TemperatureSensor:
    """
    温度传感器混入类（辅助或主温度传感器）
    Methods:
        enable_temp_meas(): 启用/禁用温度测量（子类实现）
        get_temperature(): 读取温度值（子类实现）
    ==========================================
    Temperature sensor mixin class (auxiliary or primary).
    Methods:
        enable_temp_meas(): Enable/disable temperature measurement (subclass implements)
        get_temperature(): Read temperature value (subclass implements)
    """

    def enable_temp_meas(self, enable: bool = True):
        """
        启用或禁用温度测量
        Args:
            enable (bool): True=启用，False=禁用，默认True
        Raises:
            NotImplementedError: 子类未实现
        ==========================================
        Enable or disable temperature measurement.
        Args:
            enable (bool): True=enable, False=disable, default True
        Raises:
            NotImplementedError: Subclass not implemented
        """
        raise NotImplementedError

    def get_temperature(self):
        """
        读取传感器温度值
        Returns:
            float: 温度值（摄氏度）
        Raises:
            NotImplementedError: 子类未实现
        ==========================================
        Read sensor temperature value.
        Returns:
            float: Temperature in Celsius
        Raises:
            NotImplementedError: Subclass not implemented
        """
        raise NotImplementedError


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
