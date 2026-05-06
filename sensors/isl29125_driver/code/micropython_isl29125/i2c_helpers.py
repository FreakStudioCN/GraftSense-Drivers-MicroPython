# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 12:00
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C寄存器通信辅助类，提供位域读写（CBits）和结构体寄存器读写（RegisterStruct）
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
    I2C寄存器位域读写描述符
    Attributes:
        bit_mask (int): 位掩码
        register (int): 寄存器地址
        star_bit (int): 起始位偏移
        lenght (int): 寄存器字节宽度
        lsb_first (bool): 是否小端序
    Methods:
        __get__: 读取位域值
        __set__: 写入位域值
    Notes:
        - 作为类属性描述符使用，宿主类须有 _i2c 和 _address 属性
        - 基于 adafruit_register.i2c_bits，作者 Scott Shawcroft
    ==========================================
    I2C register bit-field read/write descriptor.
    Attributes:
        bit_mask (int): Bit mask
        register (int): Register address
        star_bit (int): Start bit offset
        lenght (int): Register byte width
        lsb_first (bool): Whether LSB-first byte order
    Methods:
        __get__: Read bit-field value
        __set__: Write bit-field value
    Notes:
        - Used as class-level descriptor; host class must have _i2c and _address attributes
        - Based on adafruit_register.i2c_bits by Scott Shawcroft
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
        初始化位域描述符
        Args:
            num_bits (int): 位域宽度（位数）
            register_address (int): 寄存器地址
            start_bit (int): 位域起始位（LSB位置）
            register_width (int): 寄存器字节宽度，默认1
            lsb_first (bool): 字节序，True为小端，默认True
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize bit-field descriptor.
        Args:
            num_bits (int): Bit-field width in bits
            register_address (int): Register address
            start_bit (int): Start bit position (LSB)
            register_width (int): Register byte width, default 1
            lsb_first (bool): Byte order, True=little-endian, default True
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        # 计算位掩码：num_bits个1左移start_bit位
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.star_bit = start_bit
        self.lenght = register_width
        self.lsb_first = lsb_first

    def __get__(self, obj, objtype=None) -> int:
        """
        读取位域值
        Args:
            obj: 宿主对象，须有 _i2c 和 _address 属性
            objtype: 宿主类型（未使用）
        Returns:
            int: 位域当前值（已右移对齐）
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read bit-field value.
        Args:
            obj: Host object with _i2c and _address attributes
            objtype: Host type (unused)
        Returns:
            int: Current bit-field value (right-shifted and masked)
        Notes:
            - ISR-safe: No
        """
        # 从I2C读取寄存器原始字节
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 按字节序组合为整数
        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 提取目标位域并右移对齐
        reg = (reg & self.bit_mask) >> self.star_bit
        return reg

    def __set__(self, obj, value: int) -> None:
        """
        写入位域值
        Args:
            obj: 宿主对象，须有 _i2c 和 _address 属性
            value (int): 待写入的位域值（未移位的原始值）
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 副作用：先读后写，保留寄存器其他位不变
        ==========================================
        Write bit-field value.
        Args:
            obj: Host object with _i2c and _address attributes
            value (int): Bit-field value to write (unshifted)
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Read-modify-write, preserves other bits in register
        """
        # 读取寄存器当前值
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 按字节序组合为整数
        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]

        # 清除目标位域，写入新值
        reg &= ~self.bit_mask
        value <<= self.star_bit
        reg |= value

        # 转换为字节并写回寄存器
        reg = reg.to_bytes(self.lenght, "big")
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    I2C寄存器结构体读写描述符
    Attributes:
        format (str): struct格式字符串
        register (int): 寄存器地址
        lenght (int): 数据字节长度
    Methods:
        __get__: 读取并解包寄存器值
        __set__: 打包并写入寄存器值
    Notes:
        - 作为类属性描述符使用，宿主类须有 _i2c 和 _address 属性
        - 基于 adafruit_register.i2c_struct，作者 Scott Shawcroft
    ==========================================
    I2C register struct read/write descriptor.
    Attributes:
        format (str): struct format string
        register (int): Register address
        lenght (int): Data byte length
    Methods:
        __get__: Read and unpack register value
        __set__: Pack and write register value
    Notes:
        - Used as class-level descriptor; host class must have _i2c and _address attributes
        - Based on adafruit_register.i2c_struct by Scott Shawcroft
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化寄存器结构体描述符
        Args:
            register_address (int): 寄存器地址
            form (str): struct格式字符串（如 "B"=uint8, "h"=int16）
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize register struct descriptor.
        Args:
            register_address (int): Register address
            form (str): struct format string (e.g. "B"=uint8, "h"=int16)
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        self.format = form
        self.register = register_address
        # 根据格式字符串计算字节长度
        self.lenght = struct.calcsize(form)

    def __get__(self, obj, objtype=None):
        """
        读取并解包寄存器值
        Args:
            obj: 宿主对象，须有 _i2c 和 _address 属性
            objtype: 宿主类型（未使用）
        Returns:
            单值格式（<=2字节）返回标量，多值格式返回tuple
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read and unpack register value.
        Args:
            obj: Host object with _i2c and _address attributes
            objtype: Host type (unused)
        Returns:
            Scalar for single-value formats (<=2 bytes), tuple for multi-value formats
        Notes:
            - ISR-safe: No
        """
        if self.lenght <= 2:
            # 单值：直接返回解包后的标量
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )[0]
        else:
            # 多值：返回完整tuple
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )
        return value

    def __set__(self, obj, value: int) -> None:
        """
        打包并写入寄存器值
        Args:
            obj: 宿主对象，须有 _i2c 和 _address 属性
            value (int): 待写入的整数值
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 副作用：直接覆盖写入寄存器，不做读-改-写
        ==========================================
        Pack and write register value.
        Args:
            obj: Host object with _i2c and _address attributes
            value (int): Integer value to write
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Direct write to register, no read-modify-write
        """
        # 将整数打包为大端字节序后写入寄存器
        mem_value = value.to_bytes(self.lenght, "big")
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
