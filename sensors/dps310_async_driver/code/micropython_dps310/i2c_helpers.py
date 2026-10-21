# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/30 下午5:30
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C通信辅助工具，实现寄存器位操作、结构体数据读写、二进制补码转换功能
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import struct

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================
def twos_complement(val: int, bits: int) -> int:
    """
    二进制补码数值转换函数，处理传感器有符号原始数据
    Args:
        val (int): 待转换的原始整数值
        bits (int): 数值的二进制位宽度

    Returns:
        int: 补码转换后的有符号整数

    Notes:
        无

    ==========================================
    Two's complement conversion function for signed sensor raw data
    Args:
        val (int): Raw integer value to convert
        bits (int): Binary bit width of the value

    Returns:
        int: Converted signed integer

    Notes:
        None
    """
    if val & (1 << (bits - 1)):
        val -= 1 << bits

    return val


# ======================================== 自定义类 ============================================
class CBits:
    """
    I2C寄存器特定位操作类，用于读取和修改寄存器指定位置的二进制位
    Attributes:
        bit_mask (int): 位掩码，用于定位目标操作位
        register (int): 目标寄存器地址
        star_bit (int): 操作位的起始位置
        lenght (int): 寄存器字节宽度
        lsb_first (bool): 是否低字节优先

    Methods:
        __get__(): 读取寄存器特定位的值
        __set__(): 设置寄存器特定位的值

    Notes:
        支持单字节/多字节寄存器操作，适配不同I2C传感器寄存器格式

    ==========================================
    I2C register specific bits operation class for reading and modifying designated register bits
    Attributes:
        bit_mask (int): Bit mask for targeting operation bits
        register (int): Target register address
        star_bit (int): Start position of operation bits
        lenght (int): Register byte width
        lsb_first (bool): Whether low byte first

    Methods:
        __get__(): Read value of specific register bits
        __set__(): Set value of specific register bits

    Notes:
        Supports single/multi-byte register operation for different I2C sensors
    """

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
    ) -> None:
        """
        位操作类初始化构造方法
        Args:
            num_bits (int): 需要操作的二进制位数
            register_address (int): 目标寄存器地址
            start_bit (int): 操作位的起始位索引
            register_width (int): 寄存器字节长度，默认1字节
            lsb_first (bool): 低字节优先标志，默认True

        Returns:
            None: 无返回值

        Notes:
            自动计算位掩码用于后续位操作

        ==========================================
        Initialization constructor for bits operation class
        Args:
            num_bits (int): Number of binary bits to operate
            register_address (int): Target register address
            start_bit (int): Start index of operation bits
            register_width (int): Register byte length, default 1 byte
            lsb_first (bool): Low byte first flag, default True

        Returns:
            None: No return value

        Notes:
            Auto calculate bit mask for subsequent operations
        """
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.star_bit = start_bit
        self.lenght = register_width
        self.lsb_first = lsb_first

    def __get__(
        self,
        obj,
        objtype: type | None = None,
    ) -> int:
        """
        描述符获取方法，读取寄存器特定位的数值
        Args:
            obj: 传感器实例对象
            objtype (type | None): 实例类型，默认None

        Returns:
            int: 寄存器特定位提取后的数值

        Raises:
            ValueError: 传感器实例为None时抛出

        Notes:
            支持高低字节顺序切换

        ==========================================
        Descriptor get method to read value of specific register bits
        Args:
            obj: Sensor instance object
            objtype (type | None): Instance type, default None

        Returns:
            int: Extracted value from specific register bits

        Raises:
            ValueError: Raised if sensor instance is None

        Notes:
            Supports high/low byte order switching
        """
        if obj is None:
            raise ValueError("Sensor instance cannot be None")
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj, value: int) -> None:
        """
        描述符设置方法，写入数值到寄存器特定位
        Args:
            obj: 传感器实例对象
            value (int): 待写入的数值

        Raises:
            ValueError: 传感器实例为None时抛出

        Returns:
            None: 无返回值

        Notes:
            先读取原寄存器值，修改指定位后回写

        ==========================================
        Descriptor set method to write value to specific register bits
        Args:
            obj: Sensor instance object
            value (int): Value to write

        Raises:
            ValueError: Raised if sensor instance is None

        Returns:
            None: No return value

        Notes:
            Read original register value first, modify specific bits then write back
        """
        if obj is None:
            raise ValueError("Sensor instance cannot be None")
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]
        reg &= ~self.bit_mask

        value <<= self.star_bit
        reg |= value
        reg = reg.to_bytes(self.lenght, "big")

        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    I2C寄存器结构体操作类，实现寄存器数据的结构化读写
    Attributes:
        format (str): 数据格式化字符串，遵循struct模块格式
        register (int): 目标寄存器地址
        lenght (int): 数据字节长度

    Methods:
        __get__(): 结构化读取寄存器数据
        __set__(): 结构化写入数据到寄存器

    Notes:
        基于struct模块实现数据打包/解包，适配不同数据类型

    ==========================================
    I2C register struct operation class for structured register data read/write
    Attributes:
        format (str): Data format string following struct module rules
        register (int): Target register address
        lenght (int): Data byte length

    Methods:
        __get__(): Structured read register data
        __set__(): Structured write data to register

    Notes:
        Data pack/unpack based on struct module for different data types
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        寄存器结构体类初始化构造方法
        Args:
            register_address (int): 目标寄存器地址
            form (str): struct模块数据格式化字符串

        Returns:
            None: 无返回值

        Notes:
            自动计算格式化数据的字节长度

        ==========================================
        Initialization constructor for register struct class
        Args:
            register_address (int): Target register address
            form (str): Struct module data format string

        Returns:
            None: No return value

        Notes:
            Auto calculate byte length of formatted data
        """
        self.format = form
        self.register = register_address
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj,
        objtype: type | None = None,
    ):
        """
        描述符获取方法，结构化读取寄存器数据
        Args:
            obj: 传感器实例对象
            objtype (type | None): 实例类型，默认None

        Returns:
            Any: 解包后的结构化数据

        Raises:
            ValueError: 传感器实例为None时抛出

        Notes:
            短数据直接返回单值，长数据返回元组

        ==========================================
        Descriptor get method for structured register data read
        Args:
            obj: Sensor instance object
            objtype (type | None): Instance type, default None

        Returns:
            Any: Unpacked structured data

        Raises:
            ValueError: Raised if sensor instance is None

        Notes:
            Return single value for short data, tuple for long data
        """
        if obj is None:
            raise ValueError("Sensor instance cannot be None")
        if self.lenght <= 2:
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )[0]
        else:
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )
        return value

    def __set__(self, obj, value) -> None:
        """
        描述符设置方法，结构化写入数据到寄存器
        Args:
            obj: 传感器实例对象
            value: 待写入的结构化数据

        Raises:
            ValueError: 传感器实例为None时抛出

        Returns:
            None: 无返回值

        Notes:
            自动打包数据后写入I2C寄存器

        ==========================================
        Descriptor set method for structured data write to register
        Args:
            obj: Sensor instance object
            value: Structured data to write

        Raises:
            ValueError: Raised if sensor instance is None

        Returns:
            None: No return value

        Notes:
            Auto pack data then write to I2C register
        """
        if obj is None:
            raise ValueError("Sensor instance cannot be None")
        mem_value = struct.pack(self.format, value)
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
