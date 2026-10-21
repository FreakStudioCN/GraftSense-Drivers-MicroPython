# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午7:00
# @Author  : jposada202020
# @File    : i2c_helpers.py
# @Description : I2C通信辅助工具类，提供位操作（CBits）和结构体操作（RegisterStruct）功能，简化I2C设备寄存器读写 参考自:https://github.com/jposada202020/MicroPython_BMA220
# @License : MIT

__version__ = "0.1.0"
__author__ = "jposada202020"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入struct模块，用于数据的打包和解包
import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
    I2C寄存器位操作辅助类
    用于读取和修改I2C设备指定寄存器中的特定位段，支持多字节寄存器、LSB/MSB优先模式，简化位操作流程
    Attributes:
        bit_mask: 位掩码，用于提取或屏蔽目标位段
        register: 目标寄存器地址
        star_bit: 位段的起始位（注意：原代码拼写错误为star_bit，应为start_bit）
        lenght: 寄存器宽度（字节数），默认1字节
        lsb_first: 是否按LSB优先顺序处理多字节数据，默认True

    Methods:
        __get__: 读取寄存器中指定的位段值
        __set__: 修改寄存器中指定的位段值

    Notes:
        1. 原代码中start_bit拼写错误为star_bit，需注意使用时的兼容性
        2. 多字节处理时，order变量控制字节顺序，LSB优先时从最后一个字节开始
        3. 位操作会先读取寄存器原有值，修改目标位段后再写回

    ==========================================
    I2C Register Bit Operation Helper Class
    Used to read and modify specific bit fields in the specified register of I2C devices,
    supporting multi-byte registers, LSB/MSB first mode, simplifying bit operation process
    Attributes:
        bit_mask: Bit mask for extracting or masking target bit fields
        register: Target register address
        star_bit: Start bit of the bit field (Note: typo in original code, should be start_bit)
        lenght: Register width (number of bytes), default 1 byte
        lsb_first: Whether to process multi-byte data in LSB first order, default True

    Methods:
        __get__: Read the value of the specified bit field in the register
        __set__: Modify the value of the specified bit field in the register

    Notes:
        1. Typo in original code: start_bit is written as star_bit, pay attention to compatibility when using
        2. When processing multi-byte data, the order variable controls the byte order, starting from the last byte in LSB first mode
        3. Bit operations first read the original register value, modify the target bit field, then write back
    """

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width=1,
        lsb_first=True,
    ) -> None:
        """
        CBits类初始化方法
        Args:
            num_bits: 要操作的位段长度（位数）
            register_address: 目标寄存器地址
            start_bit: 位段的起始位
            register_width: 寄存器宽度（字节数），默认1
            lsb_first: 是否按LSB优先处理多字节数据，默认True

        Raises:
            无

        Notes:
            1. 位掩码计算方式：((1 << num_bits) - 1) << start_bit，生成连续的num_bits位掩码
            2. 原代码中register_width参数赋值给self.lenght（拼写错误，应为length）
            3. start_bit参数最终赋值给self.star_bit（拼写错误）

        ==========================================
        CBits Class Initialization Method
        Args:
            num_bits: Length of the bit field to operate (number of bits)
            register_address: Target register address
            start_bit: Start bit of the bit field
            register_width: Register width (number of bytes), default 1
            lsb_first: Whether to process multi-byte data in LSB first order, default True

        Raises:
            None

        Notes:
            1. Bit mask calculation: ((1 << num_bits) - 1) << start_bit, generates continuous num_bits bit mask
            2. register_width parameter is assigned to self.lenght (typo, should be length) in original code
            3. start_bit parameter is finally assigned to self.star_bit (typo)
        """
        # 计算位掩码，用于提取或屏蔽目标位段
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        # 存储目标寄存器地址
        self.register = register_address
        # 存储位段起始位（原代码拼写错误）
        self.star_bit = start_bit
        # 存储寄存器宽度（字节数，原代码拼写错误）
        self.lenght = register_width
        # 存储多字节数据处理顺序标识
        self.lsb_first = lsb_first

    def __get__(
        self,
        obj,
        objtype=None,
    ) -> int:
        """
        读取寄存器中指定的位段值（描述符get方法）
        Args:
            obj: 实例对象，需包含_i2c（I2C总线对象）和_address（设备I2C地址）属性
            objtype: 类类型，默认None

        Returns:
            int: 提取出的位段整数值

        Raises:
            无

        Notes:
            1. 先读取寄存器的原始字节数据，再按指定顺序拼接成整数
            2. 通过位掩码提取目标位段，并右移到最低位返回

        ==========================================
        Read the value of the specified bit field in the register (descriptor get method)
        Args:
            obj: Instance object, must contain _i2c (I2C bus object) and _address (device I2C address) attributes
            objtype: Class type, default None

        Returns:
            int: Extracted integer value of the bit field

        Raises:
            None

        Notes:
            1. First read the original byte data of the register, then splice into an integer in the specified order
            2. Extract the target bit field through bit mask and shift right to the lowest bit to return
        """
        # 从I2C设备读取指定寄存器的字节数据
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 初始化寄存器整数值
        reg = 0
        # 定义字节遍历顺序：LSB优先时从最后一个字节开始
        order = range(len(mem_value) - 1, -1, -1)
        # 如果不是LSB优先，反转遍历顺序（MSB优先）
        if not self.lsb_first:
            order = reversed(order)
        # 按顺序拼接字节为整数
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 提取目标位段并右移到最低位
        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj, value: int) -> None:
        """
        修改寄存器中指定的位段值（描述符set方法）
        Args:
            obj: 实例对象，需包含_i2c（I2C总线对象）和_address（设备I2C地址）属性
            value: 要设置的位段整数值

        Raises:
            无

        Notes:
            1. 先读取寄存器原有值，保留非目标位段数据，仅修改目标位段
            2. 将修改后的整数值转换为字节数组，写回寄存器
            3. 多字节处理时的字节顺序与读取逻辑一致

        ==========================================
        Modify the value of the specified bit field in the register (descriptor set method)
        Args:
            obj: Instance object, must contain _i2c (I2C bus object) and _address (device I2C address) attributes
            value: Integer value to set for the bit field

        Raises:
            None

        Notes:
            1. First read the original register value, retain non-target bit field data, only modify the target bit field
            2. Convert the modified integer value to a byte array and write back to the register
            3. Byte order in multi-byte processing is consistent with reading logic
        """
        # 读取寄存器原有字节数据
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 初始化寄存器整数值
        reg = 0
        # 定义字节遍历顺序：LSB优先时从最后一个字节开始
        order = range(len(memory_value) - 1, -1, -1)
        # 如果不是LSB优先，使用正向遍历顺序（MSB优先）
        if not self.lsb_first:
            order = range(0, len(memory_value))
        # 按顺序拼接字节为整数
        for i in order:
            reg = (reg << 8) | memory_value[i]
        # 清空目标位段（保留其他位数据）
        reg &= ~self.bit_mask

        # 将待设置值左移到目标位段位置
        value <<= self.star_bit
        # 将新值合并到寄存器整数中
        reg |= value
        # 将整数转换为指定长度的字节数组（大端序）
        reg = reg.to_bytes(self.lenght, "big")

        # 将修改后的字节数据写回寄存器
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    I2C寄存器结构体操作辅助类
    用于按指定格式读取和写入I2C设备寄存器的数值，支持单值和多值结构体，简化数据打包/解包流程
    Attributes:
        format: struct格式字符串，定义数据的打包/解包格式
        register: 目标寄存器地址
        lenght: 寄存器数据长度（字节数），由format计算得出

    Methods:
        __get__: 读取寄存器数据并按格式解包
        __set__: 将数值按格式打包并写入寄存器

    Notes:
        1. 支持的format格式参考Python struct模块规范
        2. 数据长度≤2字节时返回单个值，否则返回解包后的元组
        3. 写入时自动将数值打包为指定格式的字节数组

    ==========================================
    I2C Register Struct Operation Helper Class
    Used to read and write values of I2C device registers in the specified format,
    supporting single-value and multi-value structs, simplifying data packing/unpacking process
    Attributes:
        format: struct format string, defining the packing/unpacking format of data
        register: Target register address
        lenght: Register data length (number of bytes), calculated from format

    Methods:
        __get__: Read register data and unpack in the specified format
        __set__: Pack the value in the specified format and write to the register

    Notes:
        1. Supported format specifications refer to Python struct module
        2. Returns a single value when data length ≤ 2 bytes, otherwise returns unpacked tuple
        3. Automatically pack values into byte array of specified format when writing
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        RegisterStruct类初始化方法
        Args:
            register_address: 目标寄存器地址
            form: struct格式字符串，如'B'（1字节无符号字符）、'h'（2字节短整型）等

        Raises:
            无

        Notes:
            1. lenght属性由struct.calcsize(form)计算，代表格式对应的字节数
            2. form参数最终存储为self.format属性

        ==========================================
        RegisterStruct Class Initialization Method
        Args:
            register_address: Target register address
            form: struct format string, such as 'B' (1-byte unsigned char), 'h' (2-byte short integer), etc.

        Raises:
            None

        Notes:
            1. lenght attribute is calculated by struct.calcsize(form), representing the number of bytes corresponding to the format
            2. form parameter is finally stored as self.format attribute
        """
        # 存储struct格式字符串
        self.format = form
        # 存储目标寄存器地址
        self.register = register_address
        # 计算格式对应的字节长度
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj,
        objtype=None,
    ):
        """
        读取寄存器数据并按格式解包（描述符get方法）
        Args:
            obj: 实例对象，需包含_i2c（I2C总线对象）和_address（设备I2C地址）属性
            objtype: 类类型，默认None

        Returns:
            任意类型: 解包后的数值，长度≤2字节返回单个值，否则返回元组

        Raises:
            无

        Notes:
            1. 使用memoryview优化字节数据访问效率
            2. struct.unpack返回元组，长度≤2字节时取第一个元素返回

        ==========================================
        Read register data and unpack in the specified format (descriptor get method)
        Args:
            obj: Instance object, must contain _i2c (I2C bus object) and _address (device I2C address) attributes
            objtype: Class type, default None

        Returns:
            Any type: Unpacked value, returns a single value when length ≤ 2 bytes, otherwise returns a tuple

        Raises:
            None

        Notes:
            1. Use memoryview to optimize byte data access efficiency
            2. struct.unpack returns a tuple, take the first element when length ≤ 2 bytes
        """
        # 数据长度≤2字节时，返回单个解包值
        if self.lenght <= 2:
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )[0]
        # 数据长度>2字节时，返回解包后的元组
        else:
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )
        return value

    def __set__(self, obj, value):
        """
        将数值按格式打包并写入寄存器（描述符set方法）
        Args:
            obj: 实例对象，需包含_i2c（I2C总线对象）和_address（设备I2C地址）属性
            value: 要写入的数值（单个值或元组，需匹配format格式）

        Raises:
            无

        Notes:
            1. struct.pack会根据format将value打包为字节数组
            2. 写入前需确保value的类型和数量与format匹配

        ==========================================
        Pack the value in the specified format and write to the register (descriptor set method)
        Args:
            obj: Instance object, must contain _i2c (I2C bus object) and _address (device I2C address) attributes
            value: Value to write (single value or tuple, must match format specification)

        Raises:
            None

        Notes:
            1. struct.pack packs value into byte array according to format
            2. Ensure the type and quantity of value match the format before writing
        """
        # 将数值按指定格式打包为字节数组
        mem_value = struct.pack(self.format, value)
        # 将字节数组写入目标寄存器
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
