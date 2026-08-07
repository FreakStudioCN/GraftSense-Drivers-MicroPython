# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 00:00
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C register helpers for bit fields and packed values
# @License : MIT

__version__ = "0.0.0+auto.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def _check_i2c_host(obj) -> None:
    if obj is None:
        raise ValueError("obj must not be None")
    if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
        raise ValueError("obj must provide _i2c and _address")


# ======================================== 自定义类 ============================================


class CBits:
    """I2C register bit-field descriptor."""

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
    ) -> None:
        """创建寄存器位域描述符 / Create a register bit-field descriptor.

        Args:
            num_bits (int): 位域宽度 / Bit-field width.
            register_address (int): 寄存器地址 / Register address.
            start_bit (int): 起始位 / Starting bit.
            register_width (int): 寄存器宽度 / Register width.
            lsb_first (bool): 是否低位优先 / Whether bits are LSB-first.
        """
        if not isinstance(num_bits, int):
            raise ValueError("num_bits must be int, got %s" % type(num_bits))
        if not isinstance(register_address, int):
            raise ValueError("register_address must be int, got %s" % type(register_address))
        if not isinstance(start_bit, int):
            raise ValueError("start_bit must be int, got %s" % type(start_bit))
        if not isinstance(register_width, int):
            raise ValueError("register_width must be int, got %s" % type(register_width))
        if not isinstance(lsb_first, bool):
            raise ValueError("lsb_first must be bool, got %s" % type(lsb_first))
        if num_bits < 1:
            raise ValueError("num_bits must be greater than 0")
        if register_address < 0:
            raise ValueError("register_address must be 0 or greater")
        if start_bit < 0:
            raise ValueError("start_bit must be 0 or greater")
        if register_width < 1:
            raise ValueError("register_width must be greater than 0")

        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.start_bit = start_bit
        self.length = register_width
        self.lsb_first = lsb_first

    def __get__(self, obj, objtype=None) -> int:
        if obj is None:
            raise ValueError("obj must not be None")
        if objtype is None:
            objtype = type(obj)
        _check_i2c_host(obj)

        try:
            mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.length)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X (CBits get)" % self.register) from e

        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(mem_value))
        for index in order:
            reg = (reg << 8) | mem_value[index]
        return (reg & self.bit_mask) >> self.start_bit

    def __set__(self, obj, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("value must be int, got %s" % type(value))
        if value < 0:
            raise ValueError("value must be 0 or greater")
        if obj is None:
            raise ValueError("obj must not be None")
        _check_i2c_host(obj)

        try:
            memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.length)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X (CBits set)" % self.register) from e

        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for index in order:
            reg = (reg << 8) | memory_value[index]

        reg &= ~self.bit_mask
        reg |= value << self.start_bit
        data = reg.to_bytes(self.length, "big")

        try:
            obj._i2c.writeto_mem(obj._address, self.register, data)
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X (CBits set)" % self.register) from e


class RegisterStruct:
    """I2C register descriptor using struct format strings."""

    def __init__(self, register_address: int, form: str) -> None:
        """创建寄存器结构描述符 / Create a structured-register descriptor.

        Args:
            register_address (int): 寄存器地址 / Register address.
            form (str): ``ustruct`` 格式字符串 / ``ustruct`` format string.

        Raises:
            ValueError: 当地址或格式类型无效时 / If an argument type is invalid.
        """
        if not isinstance(register_address, int):
            raise ValueError("register_address must be int, got %s" % type(register_address))
        if not isinstance(form, str):
            raise ValueError("form must be str, got %s" % type(form))
        if register_address < 0:
            raise ValueError("register_address must be 0 or greater")
        if form == "":
            raise ValueError("form must not be empty")

        self.format = form
        self.register = register_address
        self.length = struct.calcsize(form)

    def __get__(self, obj, objtype=None):
        if obj is None:
            raise ValueError("obj must not be None")
        if objtype is None:
            objtype = type(obj)
        _check_i2c_host(obj)

        try:
            raw = obj._i2c.readfrom_mem(obj._address, self.register, self.length)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X (RegisterStruct get)" % self.register) from e

        value = struct.unpack(self.format, memoryview(raw))
        if len(value) == 1:
            return value[0]
        return value

    def __set__(self, obj, value) -> None:
        if obj is None:
            raise ValueError("obj must not be None")
        _check_i2c_host(obj)

        data = struct.pack(self.format, value)
        try:
            obj._i2c.writeto_mem(obj._address, self.register, data)
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X (RegisterStruct set)" % self.register) from e


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
