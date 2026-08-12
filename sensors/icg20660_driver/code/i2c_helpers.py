# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 00:00
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C 寄存器描述符辅助类（CBits / RegisterStruct）
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import struct

# Reusable buffer for the largest supported register read (three int16 values).
_BUF = bytearray(6)

# ======================================== 全局变量 ============================================
# 复用缓冲区，最大支持 6 字节寄存器读取（3×int16 加速度/陀螺仪数据）
_BUF = bytearray(6)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class CBits:
    """
    I2C 寄存器位操作描述符类
    通过 Python 描述符协议（__get__/__set__）实现对单个寄存器中特定位域的读写
    Attributes:
        _bit_mask (int): 位掩码
        _register (int): 寄存器地址
        _start_bit (int): 起始位位置
        _length (int): 寄存器宽度（字节数）
        _lsb_first (bool): 是否 LSB 优先
    Notes:
        - 依赖宿主对象提供 _i2c、_address 属性
        - 基于 Adafruit CircuitPython 设计模式
    ==========================================
    I2C register bit-field descriptor class.
    Provides read/write access to specific bit fields within a register
    via the Python descriptor protocol (__get__/__set__).
    Notes:
        - Requires host object to provide _i2c and _address attributes
        - Based on Adafruit CircuitPython design pattern
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
            num_bits (int): 位域宽度（bit 数）
            register_address (int): 寄存器地址
            start_bit (int): 起始位位置（0 = LSB）
            register_width (int): 寄存器宽度（字节数），默认 1
            lsb_first (bool): 是否 LSB 优先字节序，默认 True
        Raises:
            ValueError: 参数类型或值无效
        ==========================================
        Initialize bit-field descriptor.
        Args:
            num_bits (int): Bit-field width in bits
            register_address (int): Register address
            start_bit (int): Start bit position (0 = LSB)
            register_width (int): Register width in bytes, default 1
            lsb_first (bool): LSB-first byte order, default True
        Raises:
            ValueError: Invalid parameter type or value
        """
        # 参数校验
        if not isinstance(num_bits, int) or num_bits < 1:
            raise ValueError("num_bits must be a positive int")
        if not isinstance(register_address, int) or register_address < 0:
            raise ValueError("register_address must be a non-negative int")
        if not isinstance(start_bit, int) or start_bit < 0:
            raise ValueError("start_bit must be a non-negative int")
        if not isinstance(register_width, int) or register_width < 1:
            raise ValueError("register_width must be a positive int")

        self._bit_mask = ((1 << num_bits) - 1) << start_bit
        self._register = register_address
        self._start_bit = start_bit
        self._length = register_width
        self._lsb_first = lsb_first

    def __get__(self, obj: object, objtype: object = None) -> int:
        """
        读取寄存器位域值
        Args:
            obj: 宿主对象（需提供 _i2c 和 _address 属性）
            objtype: 宿主类型（由描述符协议自动传入）
        Returns:
            int: 位域值
        Raises:
            RuntimeError: I2C 通信失败
        ==========================================
        Read register bit-field value.
        Args:
            obj: Host object (must provide _i2c and _address)
            objtype: Host type (passed by descriptor protocol)
        Returns:
            int: Bit-field value
        Raises:
            RuntimeError: I2C communication failed
        """
        # 使用全局复用缓冲区读取寄存器
        if obj is None:
            return self
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "readfrom_mem_into"):
            raise ValueError("i2c must provide readfrom_mem_into")

        try:
            obj._i2c.readfrom_mem_into(obj._address, self._register, memoryview(_BUF)[: self._length])
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from e

        # 按字节序组装寄存器值
        reg = 0
        order = range(self._length - 1, -1, -1)
        if not self._lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | _BUF[i]

        # 应用位掩码并右移对齐
        reg = (reg & self._bit_mask) >> self._start_bit
        return reg

    def __set__(self, obj: object, value: int) -> None:
        """
        写入寄存器位域值（读-修改-写操作）
        Args:
            obj: 宿主对象（需提供 _i2c 和 _address 属性）
            value (int): 要写入的位域值
        Raises:
            ValueError: 参数类型无效
            RuntimeError: I2C 通信失败
        ==========================================
        Write register bit-field value (read-modify-write).
        Args:
            obj: Host object (must provide _i2c and _address)
            value (int): Bit-field value to write
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: I2C communication failed
        """
        if isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        if value < 0 or value > (self._bit_mask >> self._start_bit):
            raise ValueError("value does not fit the configured bit field")
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "readfrom_mem_into") or not hasattr(obj._i2c, "writeto_mem"):
            raise ValueError("i2c must provide readfrom_mem_into and writeto_mem")

        # 读取当前寄存器值（使用全局复用缓冲区）
        try:
            obj._i2c.readfrom_mem_into(obj._address, self._register, memoryview(_BUF)[: self._length])
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from e

        # 按字节序组装寄存器值
        reg = 0
        order = range(self._length - 1, -1, -1)
        if not self._lsb_first:
            order = range(0, self._length)
        for i in order:
            reg = (reg << 8) | _BUF[i]

        # 清除目标位域，写入新值
        reg &= ~self._bit_mask
        value <<= self._start_bit
        reg |= value

        # 将修改后的寄存器值写回硬件
        reg_bytes = reg.to_bytes(self._length, "big")
        try:
            obj._i2c.writeto_mem(obj._address, self._register, reg_bytes)
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self._register) from e


class RegisterStruct:
    """
    I2C 寄存器结构化读写描述符类
    通过 Python 描述符协议实现多字节寄存器的 struct 格式化读写
    Attributes:
        _format (str): struct 格式字符串
        _register (int): 寄存器地址
        _length (int): struct 格式对应的字节长度
    Notes:
        - 依赖宿主对象提供 _i2c、_address 属性
        - 基于 Adafruit CircuitPython 设计模式
    ==========================================
    I2C register structured read/write descriptor class.
    Provides struct-formatted multi-byte register access via the Python
    descriptor protocol.
    Notes:
        - Requires host object to provide _i2c and _address attributes
        - Based on Adafruit CircuitPython design pattern
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化寄存器结构描述符
        Args:
            register_address (int): 寄存器起始地址
            form (str): struct 格式字符串（如 "B", ">hhh"）
        Raises:
            ValueError: 参数类型或值无效
        ==========================================
        Initialize register struct descriptor.
        Args:
            register_address (int): Register start address
            form (str): struct format string (e.g. "B", ">hhh")
        Raises:
            ValueError: Invalid parameter type or value
        """
        # 参数校验
        if not isinstance(register_address, int) or register_address < 0:
            raise ValueError("register_address must be a non-negative int")
        if not isinstance(form, str) or not form:
            raise ValueError("form must be a non-empty str")

        self._format = form
        self._register = register_address
        self._length = struct.calcsize(form)

    def __get__(self, obj: object, objtype: object = None) -> object:
        """
        读取结构化寄存器数据
        Args:
            obj: 宿主对象（需提供 _i2c 和 _address 属性）
            objtype: 宿主类型（由描述符协议自动传入）
        Returns:
            int 或 tuple: 解包后的寄存器值（单字节返回 int，多字节返回 tuple）
        Raises:
            RuntimeError: I2C 通信失败
        ==========================================
        Read structured register data.
        Args:
            obj: Host object (must provide _i2c and _address)
            objtype: Host type (passed by descriptor protocol)
        Returns:
            int or tuple: Unpacked register value(s)
        Raises:
            RuntimeError: I2C communication failed
        """
        # 使用全局复用缓冲区读取寄存器
        if obj is None:
            return self
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "readfrom_mem_into"):
            raise ValueError("i2c must provide readfrom_mem_into")

        try:
            obj._i2c.readfrom_mem_into(obj._address, self._register, memoryview(_BUF)[: self._length])
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from e

        # struct 解包
        if self._length <= 2:
            value = struct.unpack(self._format, memoryview(_BUF[: self._length]))[0]
        else:
            value = struct.unpack(self._format, memoryview(_BUF[: self._length]))
        return value

    def __set__(self, obj: object, value: object) -> None:
        """
        写入结构化寄存器数据
        Args:
            obj: 宿主对象（需提供 _i2c 和 _address 属性）
            value: 要写入的值（与 struct 格式匹配）
        Raises:
            RuntimeError: I2C 通信失败
        ==========================================
        Write structured register data.
        Args:
            obj: Host object (must provide _i2c and _address)
            value: Value(s) to write (must match struct format)
        Raises:
            RuntimeError: I2C communication failed
        """
        # struct 打包
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "writeto_mem"):
            raise ValueError("i2c must provide writeto_mem")

        if isinstance(value, (tuple, list)):
            mem_value = struct.pack(self._format, *value)
        else:
            mem_value = struct.pack(self._format, value)
        try:
            obj._i2c.writeto_mem(obj._address, self._register, mem_value)
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self._register) from e


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
