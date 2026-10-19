# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Roman Shevchik
# @File    : bus_service.py
# @Description : MicroPython模块用于I/O总线操作，提供I2C和SPI总线适配器
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import math
from machine import I2C, SPI, Pin

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================
def mpy_bl(value: int) -> int:
    """
    计算整数值所占用的位数（等效于int.bit_length）
    Args:
        value (int): 输入整数值

    Returns:
        int: 值的二进制位数，若value为0则返回0

    Notes:
        MicroPython中int.bit_length()不可用，此函数为替代实现

    ==========================================
    Calculate the number of bits required to represent an integer (equivalent to int.bit_length)
    Args:
        value (int): input integer value

    Returns:
        int: number of bits, returns 0 if value is 0

    Notes:
        This is a replacement for int.bit_length() which is not available in MicroPython
    """
    if 0 == value:
        return 0
    return 1 + int(math.log2(abs(value)))


# ======================================== 自定义类 ============================================
class BusAdapter:
    """
    I/O总线适配器基类，作为具体总线（I2C/SPI）适配器的抽象接口
    Attributes:
        bus (I2C | SPI): 总线对象实例

    Methods:
        get_bus_type(): 返回总线类型
        read_register(): 从设备寄存器读取数据
        write_register(): 向设备寄存器写入数据
        read(): 从设备读取指定字节数
        read_to_buf(): 读取数据到缓冲区
        write(): 向设备写入缓冲区数据
        write_const(): 重复写入常量值
        read_buf_from_memory(): 从设备内存读取数据到缓冲区
        write_buf_to_memory(): 将缓冲区数据写入设备内存

    Notes:
        此类为抽象基类，子类需实现具体读写方法

    ==========================================
    Base class for I/O bus adapter, providing abstract interface for concrete buses (I2C/SPI)
    Attributes:
        bus (I2C | SPI): bus object instance

    Methods:
        get_bus_type(): return bus type
        read_register(): read data from device register
        write_register(): write data to device register
        read(): read specified number of bytes from device
        read_to_buf(): read data into buffer
        write(): write buffer data to device
        write_const(): write constant value repeatedly
        read_buf_from_memory(): read data from device memory into buffer
        write_buf_to_memory(): write buffer data to device memory

    Notes:
        This is an abstract base class; subclasses must implement concrete read/write methods
    """

    def __init__(self, bus: I2C | SPI) -> None:
        """
        初始化总线适配器
        Args:
            bus (I2C | SPI): 总线对象实例

        Raises:
            无

        Notes:
            无

        ==========================================
        Initialize bus adapter
        Args:
            bus (I2C | SPI): bus object instance

        Raises:
            None

        Notes:
            None
        """
        self.bus = bus

    def get_bus_type(self) -> type:
        """
        返回总线对象的类型
        Returns:
            type: 总线类型（如I2C或SPI）

        Notes:
            无

        ==========================================
        Return the type of the bus object
        Returns:
            type: bus type (e.g., I2C or SPI)

        Notes:
            None
        """
        return type(self.bus)

    def read_register(self, device_addr: int | Pin, reg_addr: int, bytes_count: int) -> bytes:
        """
        从设备寄存器读取数据（需子类实现）
        Args:
            device_addr (int | Pin): 设备地址（I2C为整型地址，SPI为片选引脚）
            reg_addr (int): 寄存器地址
            bytes_count (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        Raises:
            NotImplementedError: 子类未实现该方法

        Notes:
            抽象方法，必须由子类重写

        ==========================================
        Read data from device register (must be implemented by subclass)
        Args:
            device_addr (int | Pin): device address (integer for I2C, CS pin for SPI)
            reg_addr (int): register address
            bytes_count (int): number of bytes to read

        Returns:
            bytes: read data

        Raises:
            NotImplementedError: if not implemented by subclass

        Notes:
            Abstract method; must be overridden by subclass
        """
        raise NotImplementedError

    def write_register(self, device_addr: int | Pin, reg_addr: int, value: int | bytes | bytearray, bytes_count: int, byte_order: str) -> None:
        """
        向设备寄存器写入数据（需子类实现）
        Args:
            device_addr (int | Pin): 设备地址
            reg_addr (int): 寄存器地址
            value (int | bytes | bytearray): 要写入的值
            bytes_count (int): 要写入的字节数
            byte_order (str): 字节顺序（'little'或'big'）

        Raises:
            NotImplementedError: 子类未实现该方法

        Notes:
            抽象方法，必须由子类重写

        ==========================================
        Write data to device register (must be implemented by subclass)
        Args:
            device_addr (int | Pin): device address
            reg_addr (int): register address
            value (int | bytes | bytearray): value to write
            bytes_count (int): number of bytes to write
            byte_order (str): byte order ('little' or 'big')

        Raises:
            NotImplementedError: if not implemented by subclass

        Notes:
            Abstract method; must be overridden by subclass
        """
        raise NotImplementedError

    def read(self, device_addr: int | Pin, n_bytes: int) -> bytes:
        """
        从设备读取指定字节数的数据（需子类实现）
        Args:
            device_addr (int | Pin): 设备地址
            n_bytes (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        Raises:
            NotImplementedError: 子类未实现该方法

        Notes:
            抽象方法，必须由子类重写

        ==========================================
        Read specified number of bytes from device (must be implemented by subclass)
        Args:
            device_addr (int | Pin): device address
            n_bytes (int): number of bytes to read

        Returns:
            bytes: read data

        Raises:
            NotImplementedError: if not implemented by subclass

        Notes:
            Abstract method; must be overridden by subclass
        """
        raise NotImplementedError

    def read_to_buf(self, device_addr: int | Pin, buf: bytearray) -> bytes:
        """
        读取数据到缓冲区（需子类实现）
        Args:
            device_addr (int | Pin): 设备地址
            buf (bytearray): 目标缓冲区，长度决定读取字节数

        Returns:
            bytes: 缓冲区引用（通常为buf）

        Raises:
            NotImplementedError: 子类未实现该方法

        Notes:
            抽象方法，必须由子类重写

        ==========================================
        Read data into buffer (must be implemented by subclass)
        Args:
            device_addr (int | Pin): device address
            buf (bytearray): destination buffer, its length determines read count

        Returns:
            bytes: reference to buffer (usually buf)

        Raises:
            NotImplementedError: if not implemented by subclass

        Notes:
            Abstract method; must be overridden by subclass
        """
        raise NotImplementedError

    def write(self, device_addr: int | Pin, buf: bytes) -> None:
        """
        将缓冲区数据写入设备（需子类实现）
        Args:
            device_addr (int | Pin): 设备地址
            buf (bytes): 要写入的数据缓冲区

        Raises:
            NotImplementedError: 子类未实现该方法

        Notes:
            抽象方法，必须由子类重写

        ==========================================
        Write buffer data to device (must be implemented by subclass)
        Args:
            device_addr (int | Pin): device address
            buf (bytes): data buffer to write

        Raises:
            NotImplementedError: if not implemented by subclass

        Notes:
            Abstract method; must be overridden by subclass
        """
        raise NotImplementedError

    def write_const(self, device_addr: int | Pin, val: int, count: int) -> None:
        """
        重复写入常量值到设备（适用于填充操作）
        Args:
            device_addr (int | Pin): 设备地址
            val (int): 常量值（仅使用低8位）
            count (int): 重复次数

        Raises:
            ValueError: 当常量值占用超过8位时

        Notes:
            对于慢速总线，重复调用此方法效率较低，建议直接使用write方法

        ==========================================
        Write a constant value repeatedly to the device (useful for fill operations)
        Args:
            device_addr (int | Pin): device address
            val (int): constant value (only lower 8 bits are used)
            count (int): repeat count

        Raises:
            ValueError: if constant value requires more than 8 bits

        Notes:
            This method may be inefficient for slow buses; consider using write() directly
        """
        if 0 == count:
            return
        bl = mpy_bl(val)
        if bl > 8:
            raise ValueError(f"The value must take no more than 8 bits! Current: {bl}")
        _max = 16
        if count < _max:
            _max = count
        repeats = count // _max
        b = bytearray([val for _ in range(_max)])
        for _ in range(repeats):
            self.write(device_addr, b)
        remainder = count - _max * repeats
        if remainder:
            b = bytearray([val for _ in range(remainder)])
            self.write(device_addr, b)

    def read_buf_from_memory(self, device_addr: int | Pin, mem_addr, buf, address_size: int) -> None:
        """
        从设备内存区域读取数据到缓冲区（需子类实现）
        Args:
            device_addr (int | Pin): 设备地址
            mem_addr: 内存起始地址
            buf: 目标缓冲区，长度决定读取字节数
            address_size (int): 地址字节大小

        Raises:
            NotImplementedError: 子类未实现该方法

        Notes:
            抽象方法，必须由子类重写

        ==========================================
        Read data from device memory region into buffer (must be implemented by subclass)
        Args:
            device_addr (int | Pin): device address
            mem_addr: memory start address
            buf: destination buffer, its length determines read count
            address_size (int): size of address in bytes

        Raises:
            NotImplementedError: if not implemented by subclass

        Notes:
            Abstract method; must be overridden by subclass
        """
        raise NotImplementedError

    def write_buf_to_memory(self, device_addr: int | Pin, mem_addr, buf) -> None:
        """
        将缓冲区数据写入设备内存区域（需子类实现）
        Args:
            device_addr (int | Pin): 设备地址
            mem_addr: 内存起始地址
            buf: 源缓冲区

        Raises:
            NotImplementedError: 子类未实现该方法

        Notes:
            抽象方法，必须由子类重写

        ==========================================
        Write buffer data to device memory region (must be implemented by subclass)
        Args:
            device_addr (int | Pin): device address
            mem_addr: memory start address
            buf: source buffer

        Raises:
            NotImplementedError: if not implemented by subclass

        Notes:
            Abstract method; must be overridden by subclass
        """
        raise NotImplementedError


class I2cAdapter(BusAdapter):
    """
    I2C总线适配器，实现I2C设备的读写操作
    Attributes:
        bus (I2C): I2C总线对象

    Methods:
        write_register(): 向I2C设备寄存器写入数据
        read_register(): 从I2C设备寄存器读取数据
        read(): 从I2C设备读取数据
        read_to_buf(): 读取数据到缓冲区
        write(): 向I2C设备写入数据
        read_buf_from_memory(): 从I2C设备内存读取数据到缓冲区
        write_buf_to_memory(): 将缓冲区数据写入I2C设备内存

    Notes:
        继承自BusAdapter，利用machine.I2C的方法实现具体功能

    ==========================================
    I2C bus adapter implementing read/write operations for I2C devices
    Attributes:
        bus (I2C): I2C bus object

    Methods:
        write_register(): write data to I2C device register
        read_register(): read data from I2C device register
        read(): read data from I2C device
        read_to_buf(): read data into buffer
        write(): write data to I2C device
        read_buf_from_memory(): read data from I2C device memory into buffer
        write_buf_to_memory(): write buffer data to I2C device memory

    Notes:
        Inherits from BusAdapter, uses machine.I2C methods for implementation
    """

    def __init__(self, bus: I2C) -> None:
        """
        初始化I2C适配器
        Args:
            bus (I2C): I2C总线对象

        Raises:
            无

        Notes:
            无

        ==========================================
        Initialize I2C adapter
        Args:
            bus (I2C): I2C bus object

        Raises:
            None

        Notes:
            None
        """
        super().__init__(bus)

    def write_register(self, device_addr: int, reg_addr: int, value: int | bytes | bytearray, bytes_count: int, byte_order: str) -> None:
        """
        向I2C设备寄存器写入数据
        Args:
            device_addr (int): I2C设备地址
            reg_addr (int): 寄存器地址
            value (int | bytes | bytearray): 要写入的值
            bytes_count (int): 要写入的字节数
            byte_order (str): 字节顺序（'little'或'big'）

        Raises:
            无

        Notes:
            若value为int类型，则转换为bytes；若为bytes或bytearray则直接使用

        ==========================================
        Write data to I2C device register
        Args:
            device_addr (int): I2C device address
            reg_addr (int): register address
            value (int | bytes | bytearray): value to write
            bytes_count (int): number of bytes to write
            byte_order (str): byte order ('little' or 'big')

        Raises:
            None

        Notes:
            If value is int, convert to bytes; if bytes or bytearray use directly
        """
        buf = None
        if isinstance(value, int):
            buf = value.to_bytes(bytes_count, byte_order)
        if isinstance(value, (bytes, bytearray)):
            buf = value
        return self.bus.writeto_mem(device_addr, reg_addr, buf)

    def read_register(self, device_addr: int, reg_addr: int, bytes_count: int) -> bytes:
        """
        从I2C设备寄存器读取数据
        Args:
            device_addr (int): I2C设备地址
            reg_addr (int): 寄存器地址
            bytes_count (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        Notes:
            无

        ==========================================
        Read data from I2C device register
        Args:
            device_addr (int): I2C device address
            reg_addr (int): register address
            bytes_count (int): number of bytes to read

        Returns:
            bytes: read data

        Notes:
            None
        """
        return self.bus.readfrom_mem(device_addr, reg_addr, bytes_count)

    def read(self, device_addr: int, n_bytes: int) -> bytes:
        """
        从I2C设备读取数据
        Args:
            device_addr (int): I2C设备地址
            n_bytes (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        Notes:
            无

        ==========================================
        Read data from I2C device
        Args:
            device_addr (int): I2C device address
            n_bytes (int): number of bytes to read

        Returns:
            bytes: read data

        Notes:
            None
        """
        return self.bus.readfrom(device_addr, n_bytes)

    def read_to_buf(self, device_addr: int, buf: bytearray) -> bytes:
        """
        从I2C设备读取数据到缓冲区
        Args:
            device_addr (int): I2C设备地址
            buf (bytearray): 目标缓冲区，长度决定读取字节数

        Returns:
            bytes: 缓冲区引用

        Notes:
            无

        ==========================================
        Read data from I2C device into buffer
        Args:
            device_addr (int): I2C device address
            buf (bytearray): destination buffer, length determines read count

        Returns:
            bytes: reference to buffer

        Notes:
            None
        """
        self.bus.readfrom_into(device_addr, buf)
        return buf

    def write(self, device_addr: int, buf: bytes) -> None:
        """
        向I2C设备写入数据
        Args:
            device_addr (int): I2C设备地址
            buf (bytes): 要写入的数据缓冲区

        Returns:
            None

        Notes:
            无

        ==========================================
        Write data to I2C device
        Args:
            device_addr (int): I2C device address
            buf (bytes): data buffer to write

        Returns:
            None

        Notes:
            None
        """
        return self.bus.writeto(device_addr, buf)

    def read_buf_from_memory(self, device_addr: int, mem_addr, buf, address_size: int = 1) -> bytes:
        """
        从I2C设备内存区域读取数据到缓冲区
        Args:
            device_addr (int): I2C设备地址
            mem_addr: 内存起始地址
            buf: 目标缓冲区，长度决定读取字节数
            address_size (int): 地址字节大小（此处保留兼容性，实际未使用）

        Returns:
            bytes: 缓冲区引用

        Notes:
            扩展基类功能，利用readfrom_mem_into实现

        ==========================================
        Read data from I2C device memory region into buffer
        Args:
            device_addr (int): I2C device address
            mem_addr: memory start address
            buf: destination buffer, length determines read count
            address_size (int): size of address in bytes (kept for compatibility, not used)

        Returns:
            bytes: reference to buffer

        Notes:
            Extends base class functionality using readfrom_mem_into
        """
        self.bus.readfrom_mem_into(device_addr, mem_addr, buf)
        return buf

    def write_buf_to_memory(self, device_addr: int, mem_addr, buf) -> None:
        """
        将缓冲区数据写入I2C设备内存区域
        Args:
            device_addr (int): I2C设备地址
            mem_addr: 内存起始地址
            buf: 源缓冲区

        Returns:
            None

        Notes:
            扩展基类功能，利用writeto_mem实现

        ==========================================
        Write buffer data to I2C device memory region
        Args:
            device_addr (int): I2C device address
            mem_addr: memory start address
            buf: source buffer

        Returns:
            None

        Notes:
            Extends base class functionality using writeto_mem
        """
        return self.bus.writeto_mem(device_addr, mem_addr, buf)


class SpiAdapter(BusAdapter):
    """
    SPI总线适配器，实现SPI设备的读写操作
    Attributes:
        bus (SPI): SPI总线对象
        data_mode_pin (Pin | None): 数据/命令模式控制引脚
        use_data_mode_pin (bool): 是否使用数据模式引脚
        data_packet (bool): 当前包是否为数据包（True）或命令包（False）
        _address_index (int): 发送缓冲区中寄存器地址所在的字节索引
        _prepare_before_send_ref (callable | None): 发送前预处理函数引用

    Methods:
        prepare_func(): 获取/设置预处理函数
        read(): 从SPI设备读取数据
        read_to_buf(): 读取数据到缓冲区
        write(): 向SPI设备写入数据
        write_and_read(): 同时写入和读取数据
        read_buf_from_memory(): 从SPI设备内存读取数据到缓冲区（未实现）
        write_buf_to_memory(): 将缓冲区数据写入SPI设备内存（未实现）

    Notes:
        支持数据/命令模式引脚控制，适用于需要区分数据和命令的SPI设备（如ILI9481）

    ==========================================
    SPI bus adapter implementing read/write operations for SPI devices
    Attributes:
        bus (SPI): SPI bus object
        data_mode_pin (Pin | None): data/command mode control pin
        use_data_mode_pin (bool): whether to use data mode pin
        data_packet (bool): whether current packet is data (True) or command (False)
        _address_index (int): byte index of register address in transmit buffer
        _prepare_before_send_ref (callable | None): reference to pre-send preparation function

    Methods:
        prepare_func(): get/set preparation function
        read(): read data from SPI device
        read_to_buf(): read data into buffer
        write(): write data to SPI device
        write_and_read(): write and read simultaneously
        read_buf_from_memory(): read from SPI device memory into buffer (not implemented)
        write_buf_to_memory(): write buffer to SPI device memory (not implemented)

    Notes:
        Supports data/command mode pin control for SPI devices that need to distinguish data and commands (e.g., ILI9481)
    """

    def __init__(self, bus: SPI, data_mode: Pin = None) -> None:
        """
        初始化SPI适配器
        Args:
            bus (SPI): SPI总线对象
            data_mode (Pin | None): 数据模式控制引脚（高电平表示数据，低电平表示命令）

        Raises:
            无

        Notes:
            data_mode引脚用于区分数据包和命令包

        ==========================================
        Initialize SPI adapter
        Args:
            bus (SPI): SPI bus object
            data_mode (Pin | None): data mode control pin (high for data, low for command)

        Raises:
            None

        Notes:
            The data_mode pin is used to distinguish data packets from command packets
        """
        super().__init__(bus)
        # 数据模式控制引脚
        self.data_mode_pin = data_mode
        # 是否使用数据模式引脚
        self.use_data_mode_pin = False
        # 当前包类型标志：True=数据包，False=命令包
        self.data_packet = False
        # 发送缓冲区中寄存器地址的字节索引
        self._address_index = 0
        # 发送前预处理函数引用
        self._prepare_before_send_ref = None

    @property
    def prepare_func(self):
        """获取预处理函数引用"""
        return self._prepare_before_send_ref

    @prepare_func.setter
    def prepare_func(self, value) -> None:
        """设置预处理函数引用"""
        self._prepare_before_send_ref = value

    def _call_prepare(self, buf: bytearray) -> None:
        """
        内部方法：调用预处理函数（若已设置）
        Args:
            buf (bytearray): 要处理的缓冲区

        Returns:
            None

        Notes:
            无

        ==========================================
        Internal method: call preparation function if set
        Args:
            buf (bytearray): buffer to process

        Returns:
            None

        Notes:
            None
        """
        ref = self._prepare_before_send_ref
        if ref is not None:
            ref(buf, self._address_index)

    def read(self, device_addr: Pin, n_bytes: int) -> bytes:
        """
        从SPI设备读取数据
        Args:
            device_addr (Pin): SPI片选引脚
            n_bytes (int): 要读取的字节数

        Returns:
            bytes: 读取的数据

        Notes:
            读取期间片选引脚保持低电平

        ==========================================
        Read data from SPI device
        Args:
            device_addr (Pin): SPI chip select pin
            n_bytes (int): number of bytes to read

        Returns:
            bytes: read data

        Notes:
            Chip select pin is held low during read
        """
        try:
            device_addr.low()
            return self.bus.read(n_bytes)
        finally:
            device_addr.high()

    def read_to_buf(self, device_addr: Pin, buf: bytearray) -> bytes:
        """
        从SPI设备读取数据到缓冲区
        Args:
            device_addr (Pin): SPI片选引脚
            buf (bytearray): 目标缓冲区，长度决定读取字节数

        Returns:
            bytes: 缓冲区引用

        Notes:
            读取期间片选引脚保持低电平

        ==========================================
        Read data from SPI device into buffer
        Args:
            device_addr (Pin): SPI chip select pin
            buf (bytearray): destination buffer, length determines read count

        Returns:
            bytes: reference to buffer

        Notes:
            Chip select pin is held low during read
        """
        try:
            device_addr.low()
            self.bus.readinto(buf, 0x00)
            return buf
        finally:
            device_addr.high()

    def write(self, device_addr: Pin, buf: bytes) -> None:
        """
        向SPI设备写入数据
        Args:
            device_addr (Pin): SPI片选引脚
            buf (bytes): 要写入的数据缓冲区

        Returns:
            None

        Notes:
            若启用了数据模式引脚，则在写入前根据data_packet标志设置其电平

        ==========================================
        Write data to SPI device
        Args:
            device_addr (Pin): SPI chip select pin
            buf (bytes): data buffer to write

        Returns:
            None

        Notes:
            If data mode pin is enabled, set its level according to data_packet flag before writing
        """
        try:
            device_addr.low()
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write(buf)
        finally:
            device_addr.high()

    def write_and_read(self, device_addr: Pin, wr_buf: bytes, rd_buf: bytes) -> None:
        """
        同时向SPI设备写入数据并读取数据（全双工）
        Args:
            device_addr (Pin): SPI片选引脚
            wr_buf (bytes): 写入缓冲区
            rd_buf (bytes): 读取缓冲区

        Returns:
            None

        Notes:
            两个缓冲区长度必须相同

        ==========================================
        Write data to SPI device and simultaneously read data (full duplex)
        Args:
            device_addr (Pin): SPI chip select pin
            wr_buf (bytes): write buffer
            rd_buf (bytes): read buffer

        Returns:
            None

        Notes:
            Both buffers must have the same length
        """
        try:
            device_addr.low()
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write_readinto(wr_buf, rd_buf)
        finally:
            device_addr.high()

    def read_buf_from_memory(self, device_addr: Pin, mem_addr, buf) -> bytes:
        """
        从SPI设备内存区域读取数据到缓冲区（未实现）
        Args:
            device_addr (Pin): SPI片选引脚
            mem_addr: 内存起始地址
            buf: 目标缓冲区

        Returns:
            bytes: 无返回值，抛出NotImplementedError

        Raises:
            NotImplementedError: 此方法尚未实现

        Notes:
            待后续版本实现

        ==========================================
        Read data from SPI device memory region into buffer (not implemented)
        Args:
            device_addr (Pin): SPI chip select pin
            mem_addr: memory start address
            buf: destination buffer

        Returns:
            bytes: no return, raises NotImplementedError

        Raises:
            NotImplementedError: this method is not yet implemented

        Notes:
            To be implemented in future versions
        """
        try:
            device_addr.low()
            raise NotImplementedError
        finally:
            device_addr.high()

    def write_buf_to_memory(self, device_addr: Pin, mem_addr, buf) -> None:
        """
        将缓冲区数据写入SPI设备内存区域（未实现）
        Args:
            device_addr (Pin): SPI片选引脚
            mem_addr: 内存起始地址
            buf: 源缓冲区

        Raises:
            NotImplementedError: 此方法尚未实现

        Notes:
            待后续版本实现

        ==========================================
        Write buffer data to SPI device memory region (not implemented)
        Args:
            device_addr (Pin): SPI chip select pin
            mem_addr: memory start address
            buf: source buffer

        Raises:
            NotImplementedError: this method is not yet implemented

        Notes:
            To be implemented in future versions
        """
        try:
            device_addr.low()
            self._call_prepare(buf)
            raise NotImplementedError
        finally:
            device_addr.high()


# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================
