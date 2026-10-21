# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/1/15 下午3:00
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C通信辅助工具，提供位域和寄存器结构体访问功能
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
    从字节寄存器中修改特定位域
    Attributes:
        bit_mask (int): 位掩码
        register (int): 寄存器地址
        star_bit (int): 起始位位置
        lenght (int): 寄存器宽度（字节数）
        lsb_first (bool): 是否LSB优先

    Methods:
        __get__(): 读取位域值
        __set__(): 写入位域值

    Notes:
        用于描述符协议，支持通过类属性访问硬件寄存器中的连续位域

    ==========================================
    English description
    Change specific bit fields from a byte register
    Attributes:
        bit_mask (int): Bit mask
        register (int): Register address
        star_bit (int): Start bit position
        lenght (int): Register width in bytes
        lsb_first (bool): Whether LSB first

    Methods:
        __get__(): Read bit field value
        __set__(): Write bit field value

    Notes:
        Implements descriptor protocol for accessing continuous bit fields in hardware registers
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
        初始化CBits实例
        Args:
            num_bits (int): 位域宽度（位数）
            register_address (int): 寄存器地址
            start_bit (int): 起始位位置（从0开始）
            register_width (int): 寄存器字节宽度，默认1
            lsb_first (bool): 多字节时是否LSB优先，默认True

        Raisees:
            无

        Notes:
            构造掩码和寄存器信息供后续读写使用

        ==========================================
        English description
        Initialize CBits instance
        Args:
            num_bits (int): Bit field width in bits
            register_address (int): Register address
            start_bit (int): Start bit position (0-indexed)
            register_width (int): Register width in bytes, default 1
            lsb_first (bool): LSB first for multi-byte, default True

        Raises:
            None

        Notes:
            Construct mask and register information for subsequent read/write
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
        读取位域当前值
        Args:
            obj: 持有该描述符的实例对象
            objtype: 持有该描述符的类（可选）

        Returns:
            int: 位域当前值（已右对齐）

        Raises:
            无

        Notes:
            若通过类访问则返回描述符自身

        ==========================================
        English description
        Read current value of bit field
        Args:
            obj: Instance object holding this descriptor
            objtype: Class holding this descriptor (optional)

        Returns:
            int: Current bit field value (right-aligned)

        Raises:
            None

        Notes:
            Return the descriptor itself when accessed through class
        """
        # 显式检查obj是否为None，处理类级别访问
        if obj is None:
            return self
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
        设置位域值
        Args:
            obj: 持有该描述符的实例对象
            value (int): 待写入的值（右对齐，自动移位到正确位置）

        Raises:
            AttributeError: 当通过类访问时尝试设置属性

        Notes:
            先读后写，只修改掩码覆盖的位

        ==========================================
        English description
        Set bit field value
        Args:
            obj: Instance object holding this descriptor
            value (int): Value to write (right-aligned, will be shifted automatically)

        Raises:
            AttributeError: When trying to set attribute through class

        Notes:
            Read-modify-write, only modify bits covered by mask
        """
        # 显式检查obj是否为None，禁止通过类设置
        if obj is None:
            raise AttributeError("Cannot set attribute on class")
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
    将寄存器区域映射为结构体，支持多字节基本类型
    Attributes:
        format (str): struct模块格式字符串
        register (int): 起始寄存器地址
        lenght (int): 数据长度（字节）

    Methods:
        __get__(): 读取结构体值
        __set__(): 写入结构体值

    Notes:
        使用Python的struct模块进行打包/解包，支持标准类型如'H'、'f'等

    ==========================================
    English description
    Map a register region as a struct, support multi-byte basic types
    Attributes:
        format (str): struct module format string
        register (int): Starting register address
        lenght (int): Data length in bytes

    Methods:
        __get__(): Read struct value
        __set__(): Write struct value

    Notes:
        Use Python's struct module for packing/unpacking, supports standard types like 'H', 'f', etc.
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化RegisterStruct实例
        Args:
            register_address (int): 起始寄存器地址
            form (str): struct模块格式字符串（如'<H'、'>f'）

        Raises:
            无

        Notes:
            自动计算所需字节长度

        ==========================================
        English description
        Initialize RegisterStruct instance
        Args:
            register_address (int): Starting register address
            form (str): struct module format string (e.g. '<H', '>f')

        Raises:
            None

        Notes:
            Automatically calculate required byte length
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
        读取结构体值
        Args:
            obj: 持有该描述符的实例对象
            objtype: 持有该描述符的类（可选）

        Returns:
            int|tuple: 若格式长度<=2则返回单个值，否则返回解包后的元组

        Raises:
            无

        Notes:
            若通过类访问则返回描述符自身

        ==========================================
        English description
        Read struct value
        Args:
            obj: Instance object holding this descriptor
            objtype: Class holding this descriptor (optional)

        Returns:
            int|tuple: Single value if format length <=2 else unpacked tuple

        Raises:
            None

        Notes:
            Return the descriptor itself when accessed through class
        """
        # 显式检查obj是否为None，处理类级别访问
        if obj is None:
            return self
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
        写入结构体值
        Args:
            obj: 持有该描述符的实例对象
            value: 待写入的值（与格式字符串匹配的类型）

        Raises:
            AttributeError: 当通过类访问时尝试设置属性

        Notes:
            使用struct打包后直接写入寄存器

        ==========================================
        English description
        Write struct value
        Args:
            obj: Instance object holding this descriptor
            value: Value to write (type must match format string)

        Raises:
            AttributeError: When trying to set attribute through class

        Notes:
            Pack using struct and write directly to register
        """
        # 显式检查obj是否为None，禁止通过类设置
        if obj is None:
            raise AttributeError("Cannot set attribute on class")
        mem_value = struct.pack(self.format, value)
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
