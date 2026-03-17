# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/17 下午2:00
# @Author  : octaprog7
# @File    : ds3231.py
# @Description : DS3231高精度实时时钟驱动，支持I2C通信、时间读写、闹钟配置、片内温度读取、中断控制 参考自:https://github.com/octaprog7/DS3231
# @License : MIT
__version__ = "0.1.0"
__author__ = "octaprog7"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入系统模块
import sys

# 导入MicroPython核心模块
import micropython

# 导入MicroPython结构化数据打包解包模块
import ustruct

# 导入机器I2C总线模块
from machine import I2C

# ======================================== 全局变量 ============================================

# DS3231闹钟1与闹钟2寄存器掩码配置数组，用于配置闹钟匹配模式
# 索引0:闹钟1掩码数组 索引1:闹钟2掩码数组
_mask_alarms = (0x0E, 0x0C, 0x08, 0x00, 0x10), (0x06, 0x04, 0x00, 0x08)


# ======================================== 功能函数 ============================================


@micropython.native
def check_value(value: int | None, valid_range, error_msg: str) -> int:
    """
    校验参数值是否在有效范围内
    Args:
        value (int | None): 待校验的整数值
        valid_range: 有效取值范围
        error_msg (str): 校验失败时抛出的错误信息
    Returns:
        int: 校验通过的原始值
    Raises:
        ValueError: 数值为None或不在有效范围时抛出
    Notes:
        用于驱动中参数合法性校验，提升代码鲁棒性

    ==========================================
    Check if the parameter value is within the valid range
    Args:
        value (int | None): Integer value to be checked
        valid_range: Valid value range
        error_msg (str): Error message thrown when check fails
    Returns:
        int: Original value passed the check
    Raises:
        ValueError: Raised when value is None or out of valid range
    Notes:
        Used for parameter validity check in driver to improve code robustness
    """
    if value is None:
        raise ValueError("value parameter cannot be None")
    if value not in valid_range:
        raise ValueError(error_msg)
    return value


def bcd_to_int(bcd: int) -> int:
    """
    BCD码转换为十进制整数
    Args:
        bcd (int): 待转换的BCD码
    Returns:
        int: 转换后的十进制整数
    Notes:
        适用于RTC芯片寄存器数据解析

    ==========================================
    Convert BCD code to decimal integer
    Args:
        bcd (int): BCD code to be converted
    Returns:
        int: Converted decimal integer
    Notes:
        Suitable for RTC chip register data parsing
    """
    # 新增None检查
    if bcd is None:
        raise ValueError("bcd parameter cannot be None")
    mask = 0x0F
    result = bcd & mask
    mask = mask << 4
    result += 10 * ((bcd & mask) >> 4)
    return result


def int_to_bcd(value: int | None) -> int:
    """
    十进制整数转换为BCD码
    Args:
        value (int | None): 待转换的十进制整数
    Returns:
        int: 转换后的BCD码
    Raises:
        ValueError: 数值为None时抛出
    Notes:
        适用于RTC芯片寄存器数据写入

    ==========================================
    Convert decimal integer to BCD code
    Args:
        value (int | None): Decimal integer to be converted
    Returns:
        int: Converted BCD code
    Raises:
        ValueError: Raised when value is None
    Notes:
        Suitable for RTC chip register data writing
    """
    if value is None:
        raise ValueError("value parameter cannot be None")
    return int(str(value), 16)


# ======================================== 自定义类 ============================================


class BusAdapter:
    """
    总线适配器基类，作为IO总线与设备驱动类之间的代理类
    Attributes:
        bus (object): 硬件通信总线对象(I2C/SPI等)

    Methods:
        read_register(): 读取设备寄存器数据
        write_register(): 写入数据到设备寄存器
        read(): 读取设备指定长度数据
        write(): 写入数据到设备

    Notes:
        抽象基类，需子类实现具体总线操作方法

    ==========================================
    Base class for bus adapter, acting as a proxy between IO bus and device driver class
    Attributes:
        bus (object): Hardware communication bus object(I2C/SPI etc.)

    Methods:
        read_register(): Read device register data
        write_register(): Write data to device register
        read(): Read specified length data from device
        write(): Write data to device

    Notes:
        Abstract base class, requires subclass to implement specific bus operation methods
    """

    def __init__(self, bus: object) -> None:
        """
        总线适配器初始化
        Args:
            bus (object): 硬件通信总线对象
        Notes:
            保存总线对象供后续通信使用

        ==========================================
        Bus adapter initialization
        Args:
            bus (object): Hardware communication bus object
        Notes:
            Save bus object for subsequent communication
        """
        # 新增None检查
        if bus is None:
            raise ValueError("bus parameter cannot be None (must be a valid bus object like I2C)")
        self.bus = bus

    def read_register(self, device_addr: int, reg_addr: int, bytes_count: int) -> bytes:
        """
        读取传感器寄存器数据
        Args:
            device_addr (int): 设备在总线上的地址
            reg_addr (int): 设备内部寄存器地址
            bytes_count (int): 读取的字节数
        Returns:
            bytes: 读取到的字节数据
        Raises:
            NotImplementedError: 子类未实现时抛出
        Notes:
            抽象方法，需子类重写

        ==========================================
        Read sensor register data
        Args:
            device_addr (int): Device address on the bus
            reg_addr (int): Device internal register address
            bytes_count (int): Number of bytes to read
        Returns:
            bytes: Read byte data
        Raises:
            NotImplementedError: Raised when subclass not implemented
        Notes:
            Abstract method, need to be overridden by subclass
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if reg_addr is None:
            raise ValueError("reg_addr parameter cannot be None")
        if bytes_count is None:
            raise ValueError("bytes_count parameter cannot be None")
        raise NotImplementedError

    def write_register(self, device_addr: int, reg_addr: int, value: int | bytes | bytearray, bytes_count: int, byte_order: str) -> None:
        """
        写入数据到传感器寄存器
        Args:
            device_addr (int): 设备在总线上的地址
            reg_addr (int): 设备内部寄存器地址
            value (int | bytes | bytearray): 待写入的数据(整数/字节/字节数组)
            bytes_count (int): 写入的字节数
            byte_order (str): 字节序(big/little)
        Raises:
            NotImplementedError: 子类未实现时抛出
        Notes:
            抽象方法，需子类重写

        ==========================================
        Write data to sensor register
        Args:
            device_addr (int): Device address on the bus
            reg_addr (int): Device internal register address
            value (int | bytes | bytearray): Data to be written(int/bytes/bytearray)
            bytes_count (int): Number of bytes to write
            byte_order (str): Byte order(big/little)
        Raises:
            NotImplementedError: Raised when subclass not implemented
        Notes:
            Abstract method, need to be overridden by subclass
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if reg_addr is None:
            raise ValueError("reg_addr parameter cannot be None")
        if value is None:
            raise ValueError("value parameter cannot be None")
        if bytes_count is None:
            raise ValueError("bytes_count parameter cannot be None")
        if byte_order is None:
            raise ValueError("byte_order parameter cannot be None")
        raise NotImplementedError

    def read(self, device_addr: int, n_bytes: int) -> bytes:
        """
        从设备读取指定长度数据
        Args:
            device_addr (int): 设备在总线上的地址
            n_bytes (int): 读取字节数
        Returns:
            bytes: 读取到的字节数据
        Raises:
            NotImplementedError: 子类未实现时抛出
        Notes:
            抽象方法，需子类重写

        ==========================================
        Read specified length data from device
        Args:
            device_addr (int): Device address on the bus
            n_bytes (int): Number of bytes to read
        Returns:
            bytes: Read byte data
        Raises:
            NotImplementedError: Raised when subclass not implemented
        Notes:
            Abstract method, need to be overridden by subclass
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if n_bytes is None:
            raise ValueError("n_bytes parameter cannot be None")
        raise NotImplementedError

    def write(self, device_addr: int, buf: bytes) -> None:
        """
        写入字节数据到设备
        Args:
            device_addr (int): 设备在总线上的地址
            buf (bytes): 待写入的字节缓冲区
        Raises:
            NotImplementedError: 子类未实现时抛出
        Notes:
            抽象方法，需子类重写

        ==========================================
        Write byte data to device
        Args:
            device_addr (int): Device address on the bus
            buf (bytes): Byte buffer to be written
        Raises:
            NotImplementedError: Raised when subclass not implemented
        Notes:
            Abstract method, need to be overridden by subclass
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if buf is None:
            raise ValueError("buf parameter cannot be None")
        raise NotImplementedError


class I2cAdapter(BusAdapter):
    """
    I2C总线适配器，实现I2C总线的设备读写操作
    Attributes:
        bus (I2C): I2C总线对象

    Methods:
        write_register(): 写入数据到I2C设备寄存器
        read_register(): 从I2C设备寄存器读取数据
        read(): 从I2C设备读取数据
        read_buf_from_mem(): 从I2C设备内存读取数据到指定缓冲区
        write(): 写入数据到I2C设备
        write_buf_to_mem(): 写入缓冲区数据到I2C设备内存

    Notes:
        继承BusAdapter，实现I2C具体总线操作

    ==========================================
    I2C bus adapter, implement read and write operations for I2C bus devices
    Attributes:
        bus (I2C): I2C bus object

    Methods:
        write_register(): Write data to I2C device register
        read_register(): Read data from I2C device register
        read(): Read data from I2C device
        read_buf_from_mem(): Read data from I2C device memory to specified buffer
        write(): Write data to I2C device
        write_buf_to_mem(): Write buffer data to I2C device memory

    Notes:
        Inherit BusAdapter, implement specific I2C bus operations
    """

    def __init__(self, bus: I2C) -> None:
        """
        I2C适配器初始化
        Args:
            bus (I2C): 初始化完成的I2C总线对象
        Notes:
            调用父类构造函数保存总线对象

        ==========================================
        I2C adapter initialization
        Args:
            bus (I2C): Initialized I2C bus object
        Notes:
            Call parent constructor to save bus object
        """
        # 新增None检查
        if bus is None:
            raise ValueError("bus parameter cannot be None (must be an initialized I2C object)")
        super().__init__(bus)

    def write_register(self, device_addr: int, reg_addr: int, value: int | bytes | bytearray, bytes_count: int, byte_order: str) -> None:
        """
        写入数据到I2C设备寄存器
        Args:
            device_addr (int): I2C设备地址
            reg_addr (int): 设备寄存器地址
            value (int | bytes | bytearray): 待写入数据(整数/字节/字节数组)
            bytes_count (int): 写入字节数
            byte_order (str): 字节序
        Notes:
            自动转换整数为字节格式后写入

        ==========================================
        Write data to I2C device register
        Args:
            device_addr (int): I2C device address
            reg_addr (int): Device register address
            value (int | bytes | bytearray): Data to be written(int/bytes/bytearray)
            bytes_count (int): Number of bytes to write
            byte_order (str): Byte order
        Notes:
            Automatically convert integer to byte format before writing
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if reg_addr is None:
            raise ValueError("reg_addr parameter cannot be None")
        if value is None:
            raise ValueError("value parameter cannot be None")
        if bytes_count is None:
            raise ValueError("bytes_count parameter cannot be None")
        if byte_order is None:
            raise ValueError("byte_order parameter cannot be None")

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
            reg_addr (int): 设备寄存器地址
            bytes_count (int): 读取字节数
        Returns:
            bytes: 读取到的字节数据
        Notes:
            直接调用底层I2C读寄存器方法

        ==========================================
        Read data from I2C device register
        Args:
            device_addr (int): I2C device address
            reg_addr (int): Device register address
            bytes_count (int): Number of bytes to read
        Returns:
            bytes: Read byte data
        Notes:
            Directly call underlying I2C register read method
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if reg_addr is None:
            raise ValueError("reg_addr parameter cannot be None")
        if bytes_count is None:
            raise ValueError("bytes_count parameter cannot be None")

        return self.bus.readfrom_mem(device_addr, reg_addr, bytes_count)

    def read(self, device_addr: int, n_bytes: int) -> bytes:
        """
        从I2C设备读取指定长度数据
        Args:
            device_addr (int): I2C设备地址
            n_bytes (int): 读取字节数
        Returns:
            bytes: 读取到的字节数据
        Notes:
            无寄存器地址直接读取设备数据

        ==========================================
        Read specified length data from I2C device
        Args:
            device_addr (int): I2C device address
            n_bytes (int): Number of bytes to read
        Returns:
            bytes: Read byte data
        Notes:
            Read device data directly without register address
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if n_bytes is None:
            raise ValueError("n_bytes parameter cannot be None")

        return self.bus.readfrom(device_addr, n_bytes)

    def read_buf_from_mem(self, device_addr: int, mem_addr: int, buf: bytearray) -> None:
        """
        从I2C设备内存读取数据到指定缓冲区
        Args:
            device_addr (int): I2C设备地址
            mem_addr (int): 设备内存地址
            buf (bytearray): 数据存储缓冲区
        Notes:
            直接填充数据到传入缓冲区，减少内存开销

        ==========================================
        Read data from I2C device memory to specified buffer
        Args:
            device_addr (int): I2C device address
            mem_addr (int): Device memory address
            buf (bytearray): Data storage buffer
        Notes:
            Fill data directly into incoming buffer to reduce memory overhead
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if mem_addr is None:
            raise ValueError("mem_addr parameter cannot be None")
        if buf is None:
            raise ValueError("buf parameter cannot be None")

        return self.bus.readfrom_mem_into(device_addr, mem_addr, buf)

    def write(self, device_addr: int, buf: bytes) -> None:
        """
        写入字节数据到I2C设备
        Args:
            device_addr (int): I2C设备地址
            buf (bytes): 待写入字节数据
        Notes:
            无寄存器地址直接写入设备数据

        ==========================================
        Write byte data to I2C device
        Args:
            device_addr (int): I2C device address
            buf (bytes): Byte data to be written
        Notes:
            Write device data directly without register address
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if buf is None:
            raise ValueError("buf parameter cannot be None")

        return self.bus.writeto(device_addr, buf)

    def write_buf_to_mem(self, device_addr: int, mem_addr: int, buf: bytes) -> None:
        """
        写入缓冲区数据到I2C设备内存
        Args:
            device_addr (int): I2C设备地址
            mem_addr (int): 设备内存地址
            buf (bytes): 待写入数据缓冲区
        Notes:
            批量写入数据到设备指定内存地址

        ==========================================
        Write buffer data to I2C device memory
        Args:
            device_addr (int): I2C device address
            mem_addr (int): Device memory address
            buf (bytes): Data buffer to be written
        Notes:
            Batch write data to specified device memory address
        """
        # 新增None检查
        if device_addr is None:
            raise ValueError("device_addr parameter cannot be None")
        if mem_addr is None:
            raise ValueError("mem_addr parameter cannot be None")
        if buf is None:
            raise ValueError("buf parameter cannot be None")

        return self.bus.writeto_mem(device_addr, mem_addr, buf)


class Device:
    """
    设备基类，提供总线通信与数据解封包基础功能
    Attributes:
        adapter (BusAdapter): 总线适配器对象
        address (int): 设备总线地址
        big_byte_order (bool): 是否为大端字节序

    Methods:
        _get_byteorder_as_str(): 获取字节序字符串标识
        unpack(): 结构化数据解包
        is_big_byteorder(): 判断是否大端字节序

    Notes:
        所有外设驱动的基类，封装通用总线操作

    ==========================================
    Base device class, provide basic functions for bus communication and data packet processing
    Attributes:
        adapter (BusAdapter): Bus adapter object
        address (int): Device bus address
        big_byte_order (bool): Whether it is big-endian byte order

    Methods:
        _get_byteorder_as_str(): Get byte order string identifier
        unpack(): Structured data unpacking
        is_big_byteorder(): Judge whether it is big-endian byte order

    Notes:
        Base class for all peripheral drivers, encapsulate general bus operations
    """

    def __init__(self, adapter: BusAdapter, address: int, big_byte_order: bool) -> None:
        """
        设备基类初始化
        Args:
            adapter (BusAdapter): 总线适配器对象
            address (int): 设备总线地址
            big_byte_order (bool): 设备寄存器字节序(True=大端 False=小端)
        Notes:
            保存总线适配器、地址与字节序配置

        ==========================================
        Base device class initialization
        Args:
            adapter (BusAdapter): Bus adapter object
            address (int): Device bus address
            big_byte_order (bool): Device register byte order(True=big-endian False=little-endian)
        Notes:
            Save bus adapter, address and byte order configuration
        """
        # 新增None检查
        if adapter is None:
            raise ValueError("adapter parameter cannot be None (must be a BusAdapter instance)")
        if address is None:
            raise ValueError("address parameter cannot be None")
        if big_byte_order is None:
            raise ValueError("big_byte_order parameter cannot be None")

        self.adapter = adapter
        self.address = address
        self.big_byte_order = big_byte_order

    def _get_byteorder_as_str(self) -> tuple[str, str]:
        """
        获取字节序对应的字符串与格式化字符
        Returns:
            tuple[str, str]: 元组(字节序字符串, 格式化字符)
        Notes:
            内部方法，用于结构化数据打包解包

        ==========================================
        Get string and format character corresponding to byte order
        Returns:
            tuple[str, str]: Tuple(byte order string, format character)
        Notes:
            Internal method, used for structured data packing and unpacking
        """
        if self.is_big_byteorder():
            return "big", ">"
        else:
            return "little", "<"

    def unpack(self, fmt_char: str, source: bytes) -> tuple:
        """
        设备数据解包，将字节流转换为对应格式数据
        Args:
            fmt_char (str): 格式字符(c/b/B/h/H/i/I/l/L/q/Q)
            source (bytes): 待解包的字节数据
        Returns:
            tuple: 解包后的数据元组
        Raises:
            ValueError: 格式字符无效时抛出
        Notes:
            基于设备字节序自动适配解包格式

        ==========================================
        Device data unpacking, convert byte stream to corresponding format data
        Args:
            fmt_char (str): Format character(c/b/B/h/H/i/I/l/L/q/Q)
            source (bytes): Byte data to be unpacked
        Returns:
            tuple: Unpacked data tuple
        Raises:
            ValueError: Raised when format character is invalid
        Notes:
            Automatically adapt unpacking format based on device byte order
        """
        # 新增None检查
        if fmt_char is None:
            raise ValueError("fmt_char parameter cannot be None")
        if source is None:
            raise ValueError("source parameter cannot be None")

        if not fmt_char:
            raise ValueError(f"Invalid length fmt_char parameter: {len(fmt_char)}")
        bo = self._get_byteorder_as_str()[1]
        return ustruct.unpack(bo + fmt_char, source)

    @micropython.native
    def is_big_byteorder(self) -> bool:
        """
        判断设备是否使用大端字节序
        Returns:
            bool: True=大端 False=小端
        Notes:
            原生代码加速，提升运行效率

        ==========================================
        Judge whether the device uses big-endian byte order
        Returns:
            bool: True=big-endian False=little-endian
        Notes:
            Native code acceleration to improve operating efficiency
        """
        return self.big_byte_order


class BaseSensor(Device):
    """
    传感器基类，继承设备基类，扩展传感器通用接口
    Attributes:
        adapter (BusAdapter): 总线适配器对象
        address (int): 设备总线地址
        big_byte_order (bool): 是否为大端字节序

    Methods:
        get_id(): 获取传感器ID
        soft_reset(): 传感器软复位

    Notes:
        抽象类，需传感器子类实现具体方法

    ==========================================
    Base sensor class, inherit device class, extend sensor general interface
    Attributes:
        adapter (BusAdapter): Bus adapter object
        address (int): Device bus address
        big_byte_order (bool): Whether it is big-endian byte order

    Methods:
        get_id(): Get sensor ID
        soft_reset(): Sensor soft reset

    Notes:
        Abstract class, sensor subclass needs to implement specific methods
    """

    def get_id(self) -> None:
        """
        获取传感器ID
        Raises:
            NotImplementedError: 子类未实现时抛出
        Notes:
            抽象方法，用于读取传感器唯一ID

        ==========================================
        Get sensor ID
        Raises:
            NotImplementedError: Raised when subclass not implemented
        Notes:
            Abstract method, used to read sensor unique ID
        """
        raise NotImplementedError

    def soft_reset(self) -> None:
        """
        传感器软复位
        Raises:
            NotImplementedError: 子类未实现时抛出
        Notes:
            抽象方法，恢复传感器默认配置

        ==========================================
        Sensor soft reset
        Raises:
            NotImplementedError: Raised when subclass not implemented
        Notes:
            Abstract method, restore sensor default configuration
        """
        raise NotImplementedError


class Iterator:
    """
    迭代器基类，支持对象迭代操作
    Attributes:
        无自定义属性

    Methods:
        __iter__(): 返回迭代器对象
        __next__(): 获取下一个迭代数据

    Notes:
        抽象迭代器类，需子类实现__next__方法

    ==========================================
    Base iterator class, support object iteration operation
    Attributes:
        No custom attributes

    Methods:
        __iter__(): Return iterator object
        __next__(): Get next iteration data

    Notes:
        Abstract iterator class, subclass needs to implement __next__ method
    """

    def __iter__(self) -> "Iterator":
        """
        返回迭代器对象自身
        Returns:
            Iterator: 迭代器实例
        Notes:
            迭代器协议必需方法

        ==========================================
        Return iterator object itself
        Returns:
            Iterator: Iterator instance
        Notes:
            Required method for iterator protocol
        """
        return self

    def __next__(self) -> tuple:
        """
        获取迭代器下一个数据
        Raises:
            NotImplementedError: 子类未实现时抛出
        Notes:
            抽象方法，需子类重写

        ==========================================
        Get next data of iterator
        Raises:
            NotImplementedError: Raised when subclass not implemented
        Notes:
            Abstract method, need to be overridden by subclass
        """
        raise NotImplementedError


class DS3231(Device, Iterator):
    """
    DS3231高精度实时时钟驱动类，支持时间读写、闹钟、温度、中断控制
    Attributes:
        adapter (BusAdapter): 总线适配器对象
        address (int): DS3231 I2C地址(默认0x68)
        _tbuf (bytearray): 时间数据读取缓冲区
        _alarm_buf (bytearray): 闹钟数据读取缓冲区

    Methods:
        _get_alarm_mask(): 获取对应闹钟的掩码数组
        _convert_hours(): 转换小时寄存器数据为十进制小时数
        _get_day_or_date(): 解析日期/星期寄存器数据
        _read_register(): 读取芯片寄存器
        _write_register(): 写入芯片寄存器
        get_status(): 获取状态寄存器
        set_status(): 设置状态寄存器
        get_alarm_flags(): 获取闹钟触发标志
        get_control(): 获取控制寄存器
        set_control(): 设置控制寄存器
        get_temperature(): 获取片内温度
        get_aging_offset(): 获取老化偏移量
        get_time(): 获取当前时间
        set_time(): 设置当前时间
        get_alarm(): 获取闹钟配置
        set_alarm(): 设置闹钟
        control_alarm_interrupt(): 闹钟中断控制
        __next__(): 迭代器获取时间

    Notes:
        兼容MicroPython，I2C通信，支持12/24小时制

    ==========================================
    DS3231 high-precision real-time clock driver class, support time read/write, alarm, temperature, interrupt control
    Attributes:
        adapter (BusAdapter): Bus adapter object
        address (int): DS3231 I2C address(default 0x68)
        _tbuf (bytearray): Time data read buffer
        _alarm_buf (bytearray): Alarm data read buffer

    Methods:
        _get_alarm_mask(): Get mask array of corresponding alarm
        _convert_hours(): Convert hour register data to decimal hour
        _get_day_or_date(): Parse date/week register data
        _read_register(): Read chip register
        _write_register(): Write chip register
        get_status(): Get status register
        set_status(): Set status register
        get_alarm_flags(): Get alarm trigger flag
        get_control(): Get control register
        set_control(): Set control register
        get_temperature(): Get on-chip temperature
        get_aging_offset(): Get aging offset
        get_time(): Get current time
        set_time(): Set current time
        get_alarm(): Get alarm configuration
        set_alarm(): Set alarm
        control_alarm_interrupt(): Alarm interrupt control
        __next__(): Get time for iterator

    Notes:
        Compatible with MicroPython, I2C communication, support 12/24 hour format
    """

    @staticmethod
    def _get_alarm_mask(alarm_id: int) -> tuple:
        """
        获取对应闹钟的掩码数组
        Args:
            alarm_id (int): 闹钟ID(0=闹钟1 1=闹钟2)
        Returns:
            tuple: 对应闹钟的掩码数组
        Notes:
            静态内部方法，用于闹钟配置

        ==========================================
        Get mask array of corresponding alarm
        Args:
            alarm_id (int): Alarm ID(0=alarm1 1=alarm2)
        Returns:
            tuple: Mask array of corresponding alarm
        Notes:
            Static internal method, used for alarm configuration
        """
        # 新增None检查
        if alarm_id is None:
            raise ValueError("alarm_id parameter cannot be None")

        return _mask_alarms[alarm_id]

    @staticmethod
    def _convert_hours(hour_byte: int) -> int:
        """
        转换小时寄存器数据为十进制小时数
        Args:
            hour_byte (int): 小时寄存器原始值
        Returns:
            int: 十进制小时数(0-23)
        Notes:
            自动识别12/24小时制并转换

        ==========================================
        Convert hour register data to decimal hour
        Args:
            hour_byte (int): Original value of hour register
        Returns:
            int: Decimal hour(0-23)
        Notes:
            Automatically identify 12/24 hour format and convert
        """
        # 新增None检查
        if hour_byte is None:
            raise ValueError("hour_byte parameter cannot be None")

        hour = bcd_to_int(hour_byte & 0x3F)
        if hour_byte & 0x40:
            hour = bcd_to_int(hour_byte & 0x1F)
            if hour_byte & 0x20:
                hour = 12 + hour_byte
        return hour

    @staticmethod
    def _get_day_or_date(value: int) -> int:
        """
        解析日期/星期寄存器数据
        Args:
            value (int): 日期/星期寄存器原始值
        Returns:
            int: 解析后的日期或星期数值
        Notes:
            根据bit6判断是日期还是星期

        ==========================================
        Parse date/week register data
        Args:
            value (int): Original value of date/week register
        Returns:
            int: Parsed date or week value
        Notes:
            Judge date or week according to bit6
        """
        # 新增None检查
        if value is None:
            raise ValueError("value parameter cannot be None")

        if 0x40 & value:
            return bcd_to_int(0x0F & value)
        else:
            return bcd_to_int(0x3F & value)

    def __init__(self, adapter: BusAdapter, address: int = 0x68) -> None:
        """
        DS3231驱动初始化
        Args:
            adapter (BusAdapter): I2C总线适配器
            address (int): DS3231 I2C地址(默认0x68)
        Notes:
            初始化缓冲区并关闭闹钟中断

        ==========================================
        DS3231 driver initialization
        Args:
            adapter (BusAdapter): I2C bus adapter
            address (int): DS3231 I2C address(default 0x68)
        Notes:
            Initialize buffer and disable alarm interrupt
        """
        # 新增None检查
        if adapter is None:
            raise ValueError("adapter parameter cannot be None")
        if address is None:
            raise ValueError("address parameter cannot be None")

        super().__init__(adapter, address, False)
        self._tbuf = bytearray(7)
        self._alarm_buf = bytearray(4)
        self.control_alarm_interrupt()

    def _read_register(self, reg_addr: int, bytes_count: int = 2) -> bytes:
        """
        读取DS3231寄存器数据
        Args:
            reg_addr (int): 寄存器地址
            bytes_count (int): 读取字节数(默认2)
        Returns:
            bytes: 寄存器字节数据
        Notes:
            内部方法，封装总线读寄存器

        ==========================================
        Read DS3231 register data
        Args:
            reg_addr (int): Register address
            bytes_count (int): Number of bytes to read(default 2)
        Returns:
            bytes: Register byte data
        Notes:
            Internal method, encapsulate bus register read operation
        """
        # 新增None检查
        if reg_addr is None:
            raise ValueError("reg_addr parameter cannot be None")
        if bytes_count is None:
            raise ValueError("bytes_count parameter cannot be None")

        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def _write_register(self, reg_addr: int, value: int, bytes_count: int = 2) -> int:
        """
        写入数据到DS3231寄存器
        Args:
            reg_addr (int): 寄存器地址
            value (int): 待写入整数值
            bytes_count (int): 写入字节数(默认2)
        Returns:
            int: 写入操作返回值
        Notes:
            内部方法，封装总线写寄存器

        ==========================================
        Write data to DS3231 register
        Args:
            reg_addr (int): Register address
            value (int): Integer value to be written
            bytes_count (int): Number of bytes to write(default 2)
        Returns:
            int: Write operation return value
        Notes:
            Internal method, encapsulate bus register write operation
        """
        # 新增None检查
        if reg_addr is None:
            raise ValueError("reg_addr parameter cannot be None")
        if value is None:
            raise ValueError("value parameter cannot be None")
        if bytes_count is None:
            raise ValueError("bytes_count parameter cannot be None")

        byte_order = self._get_byteorder_as_str()[0]
        return self.adapter.write_register(self.address, reg_addr, value, bytes_count, byte_order)

    def get_status(self) -> int:
        """
        读取DS3231状态寄存器(0x0F)
        Returns:
            int: 8位状态寄存器值
        Notes:
            包含振荡器停止、闹钟标志、32kHz输出使能

        ==========================================
        Read DS3231 status register(0x0F)
        Returns:
            int: 8-bit status register value
        Notes:
            Includes oscillator stop flag, alarm flags, 32kHz output enable
        """
        return self._read_register(0x0F, 1)[0]

    def set_status(self, new_value: int) -> int:
        """
        设置DS3231状态寄存器
        Args:
            new_value (int): 待写入的状态值
        Returns:
            int: 写入操作返回值
        Notes:
            仅支持写入32kHz使能、闹钟标志位

        ==========================================
        Set DS3231 status register
        Args:
            new_value (int): Status value to be written
        Returns:
            int: Write operation return value
        Notes:
            Only supports writing 32kHz enable and alarm flag bits
        """
        # 新增None检查
        if new_value is None:
            raise ValueError("new_value parameter cannot be None")

        return self._write_register(0x0F, new_value, 1)

    def get_alarm_flags(self, clear: bool = True) -> tuple[bool, bool]:
        """
        获取闹钟触发标志并可选择清除
        Args:
            clear (bool): 是否清除标志位(默认True)
        Returns:
            tuple[bool, bool]: 元组(闹钟2标志, 闹钟1标志)
        Notes:
            轮询方式检测闹钟触发

        ==========================================
        Get alarm trigger flags and optionally clear them
        Args:
            clear (bool): Whether to clear the flag bits(default True)
        Returns:
            tuple[bool, bool]: Tuple(alarm 2 flag, alarm 1 flag)
        Notes:
            Polling method to detect alarm trigger
        """
        # 新增None检查
        if clear is None:
            raise ValueError("clear parameter cannot be None")

        s = self.get_status()
        a2, a1 = bool(s & 0x02), bool(s & 0x01)
        if clear:
            s &= 0xFC
        self.set_status(s)
        return a2, a1

    def get_control(self) -> int:
        """
        读取DS3231控制寄存器(0x0E)
        Returns:
            int: 8位控制寄存器值
        Notes:
            包含振荡器、方波、闹钟中断等控制位

        ==========================================
        Read DS3231 control register(0x0E)
        Returns:
            int: 8-bit control register value
        Notes:
            Includes oscillator, square wave, alarm interrupt and other control bits
        """
        return self._read_register(0x0E, 1)[0]

    def set_control(self, value: int) -> int:
        """
        设置DS3231控制寄存器
        Args:
            value (int): 待写入的控制值
        Returns:
            int: 写入操作返回值
        Notes:
            需严格对照芯片手册配置

        ==========================================
        Set DS3231 control register
        Args:
            value (int): Control value to be written
        Returns:
            int: Write operation return value
        Notes:
            Must be configured in strict accordance with the chip manual
        """
        # 新增None检查
        if value is None:
            raise ValueError("value parameter cannot be None")

        return self._write_register(0x0E, value, 1)

    def get_temperature(self) -> float:
        """
        获取DS3231片内温度传感器数据
        Returns:
            float: 摄氏温度值(精度0.25℃)
        Notes:
            温度数据为电池备份区自动更新

        ==========================================
        Get DS3231 on-chip temperature sensor data
        Returns:
            float: Celsius temperature value(precision 0.25℃)
        Notes:
            Temperature data is automatically updated in the battery backup area
        """
        hi, low = self._read_register(0x11, 2)
        return self.unpack("b", hi.to_bytes(1, sys.byteorder))[0] + 0.25 * (low >> 6)

    def get_aging_offset(self) -> int:
        """
        获取DS3231频率老化偏移值
        Returns:
            int: 老化偏移寄存器值
        Notes:
            用于校准晶振频率偏差

        ==========================================
        Get DS3231 frequency aging offset value
        Returns:
            int: Aging offset register value
        Notes:
            Used to calibrate crystal oscillator frequency deviation
        """
        return self._read_register(0x10, 1)[0]

    def get_time(self) -> tuple[int, int, int, int, int, int, int, int]:
        """
        获取DS3231当前时间
        Returns:
            tuple[int, int, int, int, int, int, int, int]: 时间元组(年,月,日,时,分,秒,星期,年积日)
        Notes:
            星期范围0-6，周一为0

        ==========================================
        Get DS3231 current time
        Returns:
            tuple[int, int, int, int, int, int, int, int]: Time tuple(year, month, day, hour, minute, second, weekday, yearday)
        Notes:
            Weekday range 0-6, Monday is 0
        """
        buf, mask = self._tbuf, 0x1F
        self.adapter.read_buf_from_mem(self.address, 0, buf)
        for i, val in enumerate(buf):
            if i in (0, 1, 4, 6):
                buf[i] = bcd_to_int(val)
            if 2 == i:
                buf[i] = DS3231._convert_hours(val)
            if 5 == i:
                buf[i] = bcd_to_int(val & mask)
        return (
            2000 + buf[6],
            buf[5],
            buf[4],
            buf[2],
            buf[1],
            buf[0],
            buf[3] - 1,
            -1,
        )

    def set_time(self, local_time: tuple[int, int, int, int, int, int, int, int]) -> None:
        """
        设置DS3231当前时间
        Args:
            local_time (tuple[int, int, int, int, int, int, int, int]): 时间元组(年,月,日,时,分,秒,星期,年积日)
        Notes:
            兼容localtime()格式，星期从0开始

        ==========================================
        Set DS3231 current time
        Args:
            local_time (tuple[int, int, int, int, int, int, int, int]): Time tuple(year, month, day, hour, minute, second, weekday, yearday)
        Notes:
            Compatible with localtime() format, weekday starts from 0
        """
        # 新增None检查
        if local_time is None:
            raise ValueError("local_time parameter cannot be None")

        k = 5, 4, 3, 6, 2, 1, 0
        v = 3, 5, 6
        value = 0
        for ind in range(7):
            if ind not in v:
                value = int_to_bcd(local_time[k[ind]])
            else:
                if 3 == ind:
                    value = int_to_bcd(local_time[k[ind]] + 1)
                if 5 == ind:
                    value = 0x80 + int_to_bcd(local_time[k[ind]])
                if 6 == ind:
                    value = int_to_bcd(local_time[k[ind]] - 2000)

            self.adapter.write_buf_to_mem(self.address, ind, value.to_bytes(1, sys.byteorder))

    def get_alarm(self, alarm_id: int = 0) -> tuple[tuple, int | None]:
        """
        获取指定闹钟的配置信息
        Args:
            alarm_id (int): 闹钟ID(0=闹钟1 1=闹钟2)
        Returns:
            tuple[tuple, int | None]: (闹钟时间元组, 匹配模式值)
        Raises:
            ValueError: 闹钟ID无效时抛出
        Notes:
            闹钟1包含秒，闹钟2无秒

        ==========================================
        Get configuration information of the specified alarm
        Args:
            alarm_id (int): Alarm ID(0=alarm1 1=alarm2)
        Returns:
            tuple[tuple, int | None]: (Alarm time tuple, match mode value)
        Raises:
            ValueError: Raised when alarm ID is invalid
        Notes:
            Alarm 1 includes seconds, alarm 2 does not include seconds
        """
        # 新增None检查
        if alarm_id is None:
            raise ValueError("alarm_id parameter cannot be None")

        check_value(alarm_id, (0, 1), f"Invalid alarm_id parameter: {alarm_id}")

        mask7 = 0x80
        mask6 = 0x40
        mask7f = 0x7F

        a_buf = self._alarm_buf
        alarm_addr = 7
        if alarm_id > 0:
            alarm_addr += 4

        self.adapter.read_buf_from_mem(self.address, alarm_addr, a_buf)
        if 0 == alarm_id:
            t = bcd_to_int(mask7f & a_buf[0]), bcd_to_int(mask7f & a_buf[1]), DS3231._convert_hours(a_buf[2]), self._get_day_or_date(a_buf[3])
        else:
            t = bcd_to_int(mask7f & a_buf[0]), DS3231._convert_hours(a_buf[1]), self._get_day_or_date(a_buf[2])

        alarm_byte = 0
        _max = 4
        if alarm_id > 0:
            _max -= 1
        for i in range(_max):
            if mask7 & a_buf[i]:
                alarm_byte |= 1 << i

        if mask6 & a_buf[_max - 1]:
            alarm_byte |= mask6

        tt = self._get_alarm_mask(alarm_id)
        if alarm_byte in tt:
            alarm_byte = tt.index(alarm_byte)
        else:
            alarm_byte = None

        return t, alarm_byte

    def set_alarm(self, alarm_time: tuple, match_value: int = 2, alarm_id: int = 0) -> None:
        """
        设置指定闹钟的时间与匹配模式
        Args:
            alarm_time (tuple): 闹钟时间元组
            match_value (int): 匹配模式(0-4/0-3)
            alarm_id (int): 闹钟ID(0=闹钟1 1=闹钟2)
        Raises:
            ValueError: 参数无效时抛出
        Notes:
            闹钟1支持秒匹配，闹钟2不支持秒

        ==========================================
        Set time and match mode of the specified alarm
        Args:
            alarm_time (tuple): Alarm time tuple
            match_value (int): Match mode(0-4/0-3)
            alarm_id (int): Alarm ID(0=alarm1 1=alarm2)
        Raises:
            ValueError: Raised when parameters are invalid
        Notes:
            Alarm 1 supports second matching, alarm 2 does not support seconds
        """
        # 新增None检查
        if alarm_time is None:
            raise ValueError("alarm_time parameter cannot be None")
        if match_value is None:
            raise ValueError("match_value parameter cannot be None")
        if alarm_id is None:
            raise ValueError("alarm_id parameter cannot be None")

        check_value(alarm_id, (0, 1), f"Invalid alarm_id parameter: {alarm_id}")
        check_value(match_value, range(5 if 0 == alarm_id else 4), f"Invalid match_value parameter: {match_value}")
        a_buf = self._alarm_buf
        alarm_addr = 7
        if alarm_id > 0:
            alarm_addr += 4

        cnt, offs = 4, 0
        if alarm_id > 0:
            cnt, offs = 3, 1

        am = self._get_alarm_mask(alarm_id)[match_value]
        mask = 0
        for i in range(cnt):
            if am & (1 << i):
                mask = 0x80
            if i == cnt - 1:
                mask |= am & (1 << cnt)

            a_buf[i] = mask | int_to_bcd(alarm_time[i + offs])

        byte_order = self._get_byteorder_as_str()[0]
        self.adapter.write_register(self.address, alarm_addr, a_buf, cnt, byte_order)

    def control_alarm_interrupt(self, irq_alarm_1_enable: bool = False, irq_alarm_0_enable: bool = False) -> None:
        """
        配置闹钟中断使能
        Args:
            irq_alarm_1_enable (bool): 闹钟2中断使能
            irq_alarm_0_enable (bool): 闹钟1中断使能
        Notes:
            不使用中断可轮询get_alarm_flags检测触发

        ==========================================
        Configure alarm interrupt enable
        Args:
            irq_alarm_1_enable (bool): Alarm 2 interrupt enable
            irq_alarm_0_enable (bool): Alarm 1 interrupt enable
        Notes:
            If interrupt is not used, poll get_alarm_flags to detect trigger
        """
        # 新增None检查
        if irq_alarm_1_enable is None:
            raise ValueError("irq_alarm_1_enable parameter cannot be None")
        if irq_alarm_0_enable is None:
            raise ValueError("irq_alarm_0_enable parameter cannot be None")

        cr = self.get_control()
        cr &= 0xB8
        if irq_alarm_1_enable:
            cr |= 0x06
        if irq_alarm_0_enable:
            cr |= 0x05
        self.set_control(cr)

    def __next__(self) -> tuple[int, int, int, int, int, int, int, int]:
        """
        迭代器获取当前时间
        Returns:
            tuple[int, int, int, int, int, int, int, int]: 时间元组
        Notes:
            支持for循环迭代读取时间

        ==========================================
        Iterator to get current time
        Returns:
            tuple[int, int, int, int, int, int, int, int]: Time tuple
        Notes:
            Support for loop iteration to read time
        """
        return self.get_time()


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
