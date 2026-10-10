# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午6:00
# @Author  : Roman Shevchik
# @File    : base_sensor.py
# @Description : 传感器基类模块，提供I2C/SPI通信、寄存器访问、功耗控制等基础功能
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
def check_value(value: [int, None], valid_range: [range, tuple], error_msg: str) -> [int, None]:
    """
    检查值是否在有效范围内，若为None则直接返回。
    Args:
        value (int | None): 待检查的值
        valid_range (range | tuple): 有效范围（range或tuple）
        error_msg (str): 错误消息

    Returns:
        int | None: 原始值或None

    Raises:
        ValueError: 当value不为None且不在有效范围内时抛出

    Notes:
        使用@micropython.native装饰器优化性能

    ==========================================
    Check if value is within valid range, return directly if None.
    Args:
        value (int | None): Value to check
        valid_range (range | tuple): Valid range (range or tuple)
        error_msg (str): Error message

    Returns:
        int | None: Original value or None

    Raises:
        ValueError: Raised when value is not None and not in valid_range

    Notes:
        Decorated with @micropython.native for performance optimization
    """
    if value is None:
        return value
    if value not in valid_range:
        raise ValueError(error_msg)
    return value


def get_error_str(val_name: str, val: int, rng: [range, tuple]) -> str:
    """
    生成详细的错误消息字符串。
    Args:
        val_name (str): 变量名
        val (int): 变量值
        rng (range | tuple): 有效范围

    Returns:
        str: 错误消息

    Notes:
        无

    ==========================================
    Generate detailed error message string.
    Args:
        val_name (str): Variable name
        val (int): Variable value
        rng (range | tuple): Valid range

    Returns:
        str: Error message

    Notes:
        None
    """
    if isinstance(rng, range):
        return f"Value {val} of parameter {val_name} out of range [{rng.start}..{rng.stop - 1}]!"
    # tuple
    return f"Value {val} of parameter {val_name} out of range: {rng}!"


def all_none(*args) -> bool:
    """
    检查所有参数是否均为None。
    Args:
        *args: 可变参数列表

    Returns:
        bool: 若所有参数均为None则返回True，否则返回False

    Notes:
        添加于2024-01-25

    ==========================================
    Check if all arguments are None.
    Args:
        *args: Variable argument list

    Returns:
        bool: True if all arguments are None, False otherwise

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
    设备基类，提供字节序处理和打包/解包功能。
    Attributes:
        adapter (bus_service.BusAdapter): 总线适配器
        address (int | Pin): 设备地址或引脚
        big_byte_order (bool): 大端字节序标志
        msb_first (bool): SPI传输时是否MSB在前

    Methods:
        _get_byteorder_as_str(): 返回字节序字符串元组
        pack(): 将值打包为字节串
        unpack(): 解包字节串为值
        is_big_byteorder(): 返回大端标志

    Notes:
        此类提供底层字节序处理，不直接操作总线

    ==========================================
    Device base class providing byte order handling and packing/unpacking.
    Attributes:
        adapter (bus_service.BusAdapter): Bus adapter
        address (int | Pin): Device address or pin
        big_byte_order (bool): Big-endian flag
        msb_first (bool): MSB first flag for SPI transmission

    Methods:
        _get_byteorder_as_str(): Return byte order string tuple
        pack(): Pack values into bytes
        unpack(): Unpack bytes into values
        is_big_byteorder(): Return big-endian flag

    Notes:
        This class provides low-level byte order handling, does not directly operate the bus
    """

    def __init__(self, adapter: bus_service.BusAdapter, address: [int, Pin], big_byte_order: bool):
        """
        初始化设备实例。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int | Pin): I2C地址或SPI片选引脚
            big_byte_order (bool): True表示寄存器为大端序，False为小端序

        Notes:
            同时设置msb_first默认为True（SPI MSB优先）

        ==========================================
        Initialize device instance.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int | Pin): I2C address or SPI chip select pin
            big_byte_order (bool): True for big-endian register byte order, False for little-endian

        Notes:
            Also sets msb_first default to True (SPI MSB first)
        """
        self.adapter = adapter
        self.address = address
        # for I2C. byte order in register of device
        self.big_byte_order = big_byte_order
        # for SPI ONLY. 数据传输时SPI.firstbit可以是SPI.MSB或SPI.LSB
        # 是否先传输最高有效位
        # 每个设备单独设置
        self.msb_first = True

    def _get_byteorder_as_str(self) -> tuple:
        """
        返回字节序字符串对（用于struct模块）。
        Returns:
            tuple: (byteorder_str, struct_prefix)，例如('big', '>')或('little', '<')

        Notes:
            内部使用

        ==========================================
        Return byte order string pair for struct module.
        Returns:
            tuple: (byteorder_str, struct_prefix) e.g. ('big', '>') or ('little', '<')

        Notes:
            Internal use
        """
        if self.is_big_byteorder():
            return 'big', '>'
        return 'little', '<'

    def pack(self, fmt_char: str, *values) -> bytes:
        """
        将值打包为字节串。
        Args:
            fmt_char (str): struct格式字符（如'H','h','I'等）
            *values: 待打包的值

        Returns:
            bytes: 打包后的字节串

        Raises:
            ValueError: 如果fmt_char为空字符串

        Notes:
            使用设备当前的字节序

        ==========================================
        Pack values into bytes.
        Args:
            fmt_char (str): struct format character (e.g. 'H','h','I')
            *values: Values to pack

        Returns:
            bytes: Packed bytes

        Raises:
            ValueError: If fmt_char is empty

        Notes:
            Uses current device byte order
        """
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        return struct.pack(bo + fmt_char, values)

    def unpack(self, fmt_char: str, source: bytes, redefine_byte_order: str = None) -> tuple:
        """
        从字节串解包为值。
        Args:
            fmt_char (str): struct格式字符
            source (bytes): 源字节串
            redefine_byte_order (str | None): 可选，强制指定字节序前缀（如'>'或'<'）

        Returns:
            tuple: 解包后的值元组

        Raises:
            ValueError: 如果fmt_char为空字符串

        Notes:
            若redefine_byte_order不为None，则使用其指定的字节序

        ==========================================
        Unpack bytes into values.
        Args:
            fmt_char (str): struct format character
            source (bytes): Source bytes
            redefine_byte_order (str | None): Optional, force byte order prefix (e.g. '>' or '<')

        Returns:
            tuple: Unpacked values

        Raises:
            ValueError: If fmt_char is empty

        Notes:
            If redefine_byte_order is not None, uses that byte order
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
        返回当前是否为大端字节序。
        Returns:
            bool: True表示大端，False表示小端

        ==========================================
        Return whether current byte order is big-endian.
        Returns:
            bool: True for big-endian, False for little-endian
        """
        return self.big_byte_order


class DeviceEx(Device):
    """
    扩展设备类，添加总线读写方法。
    Attributes:
        继承自Device

    Methods:
        read_reg(): 读取寄存器
        write_reg(): 写入寄存器
        read(): 读取指定字节数
        read_to_buf(): 读取到缓冲区
        write(): 写入字节串
        read_buf_from_mem(): 从内存读取到缓冲区
        write_buf_to_mem(): 将缓冲区写入内存

    Notes:
        新增于2024-01-30

    ==========================================
    Extended device class adding bus read/write methods.
    Attributes:
        Inherited from Device

    Methods:
        read_reg(): Read register
        write_reg(): Write register
        read(): Read specified number of bytes
        read_to_buf(): Read into buffer
        write(): Write bytes
        read_buf_from_mem(): Read from memory into buffer
        write_buf_to_mem(): Write buffer to memory

    Notes:
        Added on 2024-01-30
    """

    def read_reg(self, reg_addr: int, bytes_count: int = 2) -> bytes:
        """
        从设备寄存器读取数据。
        Args:
            reg_addr (int): 寄存器地址
            bytes_count (int): 要读取的字节数，默认2

        Returns:
            bytes: 读取到的字节串

        Notes:
            调用适配器的read_register方法

        ==========================================
        Read data from device register.
        Args:
            reg_addr (int): Register address
            bytes_count (int): Number of bytes to read, default 2

        Returns:
            bytes: Read bytes

        Notes:
            Calls adapter's read_register method
        """
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def write_reg(self, reg_addr: int, value: [int, bytes, bytearray], bytes_count: int) -> int:
        """
        向设备寄存器写入数据。
        Args:
            reg_addr (int): 寄存器地址
            value (int | bytes | bytearray): 要写入的值
            bytes_count (int): 值的字节数

        Returns:
            int: 写入结果（适配器返回值）

        Notes:
            根据设备字节序打包数据后写入

        ==========================================
        Write data to device register.
        Args:
            reg_addr (int): Register address
            value (int | bytes | bytearray): Value to write
            bytes_count (int): Number of bytes of the value

        Returns:
            int: Write result (adapter return value)

        Notes:
            Packs data according to device byte order before writing
        """
        byte_order = self._get_byteorder_as_str()[0]
        return self.adapter.write_register(self.address, reg_addr, value, bytes_count, byte_order)

    def read(self, n_bytes: int) -> bytes:
        """
        从设备读取指定字节数。
        Args:
            n_bytes (int): 要读取的字节数

        Returns:
            bytes: 读取到的字节串

        Notes:
            无

        ==========================================
        Read specified number of bytes from device.
        Args:
            n_bytes (int): Number of bytes to read

        Returns:
            bytes: Read bytes

        Notes:
            None
        """
        return self.adapter.read(self.address, n_bytes)

    def read_to_buf(self, buf) -> bytes:
        """
        将设备数据读取到缓冲区。
        Args:
            buf (bytearray): 目标缓冲区

        Returns:
            bytes: 实际读取的字节串（与buf内容相同）

        Notes:
            无

        ==========================================
        Read device data into buffer.
        Args:
            buf (bytearray): Destination buffer

        Returns:
            bytes: Bytes read (same as buffer content)

        Notes:
            None
        """
        return self.adapter.read_to_buf(self.address, buf)

    def write(self, buf: bytes):
        """
        向设备写入字节串。
        Args:
            buf (bytes): 要写入的数据

        Returns:
            int: 写入结果

        Notes:
            无

        ==========================================
        Write bytes to device.
        Args:
            buf (bytes): Data to write

        Returns:
            int: Write result

        Notes:
            None
        """
        return self.adapter.write(self.address, buf)

    def read_buf_from_mem(self, address: int, buf, address_size: int = 1):
        """
        从设备内存读取数据到缓冲区。
        Args:
            address (int): 起始内存地址
            buf (bytearray): 目标缓冲区
            address_size (int): 地址字节数，默认1

        Returns:
            int: 读取结果

        Notes:
            无

        ==========================================
        Read data from device memory into buffer.
        Args:
            address (int): Starting memory address
            buf (bytearray): Destination buffer
            address_size (int): Address size in bytes, default 1

        Returns:
            int: Read result

        Notes:
            None
        """
        return self.adapter.read_buf_from_memory(self.address, address, buf, address_size)

    def write_buf_to_mem(self, mem_addr, buf):
        """
        将缓冲区数据写入设备内存。
        Args:
            mem_addr (int): 目标内存起始地址
            buf (bytes | bytearray): 要写入的数据

        Returns:
            int: 写入结果

        Notes:
            无

        ==========================================
        Write buffer data to device memory.
        Args:
            mem_addr (int): Destination memory start address
            buf (bytes | bytearray): Data to write

        Returns:
            int: Write result

        Notes:
            None
        """
        return self.adapter.write_buf_to_memory(self.address, mem_addr, buf)


class BaseSensor(Device):
    """
    传感器基类，定义ID读取和软件复位接口。
    Methods:
        get_id(): 读取设备ID（需子类实现）
        soft_reset(): 软件复位（需子类实现）

    Notes:
        继承自Device，未实现具体功能

    ==========================================
    Sensor base class defining ID read and software reset interfaces.
    Methods:
        get_id(): Read device ID (to be implemented)
        soft_reset(): Software reset (to be implemented)

    Notes:
        Inherits from Device, no concrete implementation
    """

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class BaseSensorEx(DeviceEx):
    """
    扩展传感器基类，定义ID读取和软件复位接口。
    Methods:
        get_id(): 读取设备ID（需子类实现）
        soft_reset(): 软件复位（需子类实现）

    Notes:
        继承自DeviceEx，提供更丰富的总线操作

    ==========================================
    Extended sensor base class defining ID read and software reset interfaces.
    Methods:
        get_id(): Read device ID (to be implemented)
        soft_reset(): Software reset (to be implemented)

    Notes:
        Inherits from DeviceEx, provides richer bus operations
    """

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class Iterator:
    """
    迭代器接口类。
    Methods:
        __iter__(): 返回自身
        __next__(): 获取下一个值（需子类实现）

    Notes:
        无

    ==========================================
    Iterator interface class.
    Methods:
        __iter__(): Return self
        __next__(): Get next value (to be implemented)

    Notes:
        None
    """

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError


class ITemperatureSensor:
    """
    温度传感器接口。
    Methods:
        enable_temp_meas(): 使能/禁用温度测量
        get_temperature(): 获取温度值（摄氏度）

    Notes:
        用于辅助温度测量或主温度传感器

    ==========================================
    Temperature sensor interface.
    Methods:
        enable_temp_meas(): Enable/disable temperature measurement
        get_temperature(): Get temperature (Celsius)

    Notes:
        For auxiliary or primary temperature sensors
    """

    def enable_temp_meas(self, enable: bool = True):
        """Enable/disable temperature measurement"""
        raise NotImplementedError

    def get_temperature(self) -> [int, float]:
        """Return temperature in degrees Celsius"""
        raise NotImplementedError


class IPower:
    """
    功耗管理接口。
    Methods:
        set_power_level(): 设置或查询功耗等级

    Notes:
        等级0表示全功能（最高功耗），最高等级表示最小功能（最低功耗）

    ==========================================
    Power management interface.
    Methods:
        set_power_level(): Set or query power level

    Notes:
        Level 0 means full functionality (max power consumption), maximum level means minimal functionality (min power consumption)
    """

    def set_power_level(self, level: [int, None] = 0) -> int:
        """
        设置或查询功耗等级。
        Args:
            level (int | None): 0为全功能，更大值为低功耗；若为None则仅查询

        Returns:
            int: 当前功耗等级

        Notes:
            子类应实现具体逻辑，并处理寄存器值与自定义等级间的映射

        ==========================================
        Set or query power level.
        Args:
            level (int | None): 0 for full functionality, larger value for low power; if None, query only

        Returns:
            int: Current power level

        Notes:
            Subclass should implement concrete logic and map register values to custom levels
        """
        raise NotImplemented


class IBaseSensorEx:
    """
    扩展传感器接口，定义标准测量方法。
    Methods:
        get_conversion_cycle_time(): 获取转换周期时间
        start_measurement(): 启动测量
        get_measurement_value(): 按索引获取测量值
        get_data_status(): 获取数据状态
        is_single_shot_mode(): 是否为单次模式
        is_continuously_mode(): 是否为连续模式

    Notes:
        适用于大多数传感器

    ==========================================
    Extended sensor interface defining standard measurement methods.
    Methods:
        get_conversion_cycle_time(): Get conversion cycle time
        start_measurement(): Start measurement
        get_measurement_value(): Get measurement value by index
        get_data_status(): Get data status
        is_single_shot_mode(): Check if single-shot mode
        is_continuously_mode(): Check if continuous mode

    Notes:
        Suitable for most sensors
    """

    def get_conversion_cycle_time(self) -> int:
        """Return conversion cycle time in ms or us for current settings."""
        raise NotImplemented

    def start_measurement(self):
        """Configure sensor and start measurement process."""
        raise NotImplemented

    def get_measurement_value(self, value_index: int):
        """Return measurement value(s) by index."""
        raise NotImplemented

    def get_data_status(self):
        """Return data ready status; return type is implementation defined."""
        raise NotImplemented

    def is_single_shot_mode(self) -> bool:
        """Return True if in single-shot measurement mode."""
        raise NotImplemented

    def is_continuously_mode(self) -> bool:
        """Return True if in continuous measurement mode."""
        raise NotImplemented


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
