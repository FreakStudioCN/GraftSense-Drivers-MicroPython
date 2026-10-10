# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C通信辅助类，提供位操作和寄存器结构体读写功能
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

# pylint: disable=too-many-arguments
import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
    从字节寄存器中修改特定位域
    Attributes:
        bit_mask (int): 位掩码，用于提取目标位
        register (int): 寄存器地址
        star_bit (int): 起始位位置（注意拼写错误，实际应为start_bit）
        lenght (int): 寄存器宽度（字节数）
        lsb_first (bool): 是否低位优先（影响字节序）

    Methods:
        __get__(obj, objtype): 读取位域值
        __set__(obj, value): 写入位域值

    Notes:
        该类作为描述符使用，需绑定到I2C设备对象，该对象需具有 _i2c 和 _address 属性

    ==========================================
    Modify bit fields from a byte register
    Attributes:
        bit_mask (int): Bit mask to extract target bits
        register (int): Register address
        star_bit (int): Start bit position (typo, should be start_bit)
        lenght (int): Register width in bytes
        lsb_first (bool): Whether least significant byte first

    Methods:
        __get__(obj, objtype): Read bit field value
        __set__(obj, value): Write bit field value

    Notes:
        This class acts as a descriptor and must be bound to an I2C device object
        that has _i2c and _address attributes
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
        初始化CBits描述符
        Args:
            num_bits (int): 要操作的位数
            register_address (int): 寄存器地址
            start_bit (int): 起始位位置（0表示最低位）
            register_width (int): 寄存器宽度（字节数），默认为1
            lsb_first (bool): 是否低位优先，默认为True

        Notes:
            计算位掩码并存储参数

        ==========================================
        Initialize CBits descriptor
        Args:
            num_bits (int): Number of bits to operate
            register_address (int): Register address
            start_bit (int): Start bit position (0 = LSB)
            register_width (int): Register width in bytes, default 1
            lsb_first (bool): Whether least significant byte first, default True

        Notes:
            Compute bit mask and store parameters
        """
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.star_bit = start_bit
        self.lenght = register_width
        self.lsb_first = lsb_first

    def __get__(
        self,
        obj,
        objtype=None,
    ) -> int:
        """
        读取位域值
        Args:
            obj: 宿主对象（I2C设备）
            objtype: 宿主类型（未使用）

        Returns:
            int: 提取后的位域值

        Notes:
            从I2C设备读取寄存器数据，根据字节序拼接，然后掩码提取

        ==========================================
        Read bit field value
        Args:
            obj: Host object (I2C device)
            objtype: Host type (unused)

        Returns:
            int: Extracted bit field value

        Notes:
            Read register data from I2C device, assemble bytes according to endianness,
            then mask and shift to extract field
        """
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
        写入位域值
        Args:
            obj: 宿主对象（I2C设备）
            value (int): 待写入的值（已对齐到位域范围）

        Notes:
            读取当前寄存器值，清除位域，写入新值，然后写回I2C设备

        ==========================================
        Write bit field value
        Args:
            obj: Host object (I2C device)
            value (int): Value to write (aligned to bit field range)

        Notes:
            Read current register value, clear bit field, set new value,
            then write back to I2C device
        """
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
    将寄存器映射为结构体，支持任意格式的二进制数据读写
    Attributes:
        format (str): struct格式字符串（如"<H"）
        register (int): 寄存器地址
        lenght (int): 数据长度（字节数）

    Methods:
        __get__(obj, objtype): 读取结构体数据
        __set__(obj, value): 写入结构体数据

    Notes:
        使用Python struct模块解析二进制数据，支持多字节寄存器

    ==========================================
    Map a register as a struct, supporting arbitrary binary data read/write
    Attributes:
        format (str): struct format string (e.g., "<H")
        register (int): Register address
        lenght (int): Data length in bytes

    Methods:
        __get__(obj, objtype): Read struct data
        __set__(obj, value): Write struct data

    Notes:
        Uses Python struct module to parse binary data, supports multi-byte registers
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化RegisterStruct描述符
        Args:
            register_address (int): 寄存器地址
            form (str): struct格式字符串

        Notes:
            计算数据长度并存储

        ==========================================
        Initialize RegisterStruct descriptor
        Args:
            register_address (int): Register address
            form (str): struct format string

        Notes:
            Compute data length and store
        """
        self.format = form
        self.register = register_address
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj,
        objtype=None,
    ):
        """
        读取结构体数据
        Args:
            obj: 宿主对象（I2C设备）
            objtype: 宿主类型（未使用）

        Returns:
            tuple or value: 若长度<=2且格式为单值，返回单一值；否则返回元组

        Notes:
            根据数据长度选择unpack方式，若长度<=2则直接返回单一数值，否则返回元组

        ==========================================
        Read struct data
        Args:
            obj: Host object (I2C device)
            objtype: Host type (unused)

        Returns:
            tuple or value: If length <= 2 and format yields single value, return single value;
                            otherwise return tuple

        Notes:
            Choose unpack method based on data length, return single value for length <=2,
            else return tuple
        """
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

    def __set__(self, obj, value):
        """
        写入结构体数据
        Args:
            obj: 宿主对象（I2C设备）
            value: 待写入的值（数值或元组）

        Notes:
            将值转换为大端字节序列，然后写入I2C设备

        ==========================================
        Write struct data
        Args:
            obj: Host object (I2C device)
            value: Value to write (numeric or tuple)

        Notes:
            Convert value to big-endian byte string and write to I2C device
        """
        mem_value = value.to_bytes(self.lenght, "big")
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
