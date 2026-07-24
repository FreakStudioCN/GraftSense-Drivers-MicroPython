# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Jose D. Montoya (based on Adafruit Industries by Scott Shawcroft)
# @File    : i2c_helpers.py
# @Description : I2C register bit-field and struct descriptors for ICM20948.
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya (based on Adafruit Industries by Scott Shawcroft)"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class CBits:
    """Descriptor for reading and writing a bit field in an I2C register."""

    def __init__(self, num_bits: int, register_address: int, start_bit: int, register_width: int = 1, lsb_first: bool = True) -> None:
        if not isinstance(num_bits, int):
            raise ValueError("num_bits must be int")
        if not isinstance(register_address, int):
            raise ValueError("register_address must be int")
        if not isinstance(start_bit, int):
            raise ValueError("start_bit must be int")
        if not isinstance(register_width, int):
            raise ValueError("register_width must be int")
        if not isinstance(lsb_first, bool):
            raise ValueError("lsb_first must be bool")
        if num_bits < 0:
            raise ValueError("num_bits must be zero or greater")
        if register_address < 0 or register_address > 0xFF:
            raise ValueError("register_address must be in range 0..255")
        if start_bit < 0:
            raise ValueError("start_bit must be zero or greater")
        if register_width <= 0:
            raise ValueError("register_width must be greater than zero")
        if start_bit + num_bits > register_width * 8:
            raise ValueError("bit field does not fit in register_width")

        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.start_bit = start_bit
        self.length = register_width
        self.lsb_first = lsb_first

    def __get__(self, obj, objtype=None) -> int:
        if obj is None:
            return self
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")

        try:
            mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.length)
        except OSError as exc:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self.register) from exc

        reg = 0
        if self.lsb_first:
            order = range(len(mem_value) - 1, -1, -1)
        else:
            order = range(0, len(mem_value))
        for index in order:
            reg = (reg << 8) | mem_value[index]
        return (reg & self.bit_mask) >> self.start_bit

    def __set__(self, obj, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("value must be int")
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        max_value = self.bit_mask >> self.start_bit
        if value < 0 or value > max_value:
            raise ValueError("value does not fit in bit field")

        try:
            memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.length)
        except OSError as exc:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self.register) from exc

        reg = 0
        if self.lsb_first:
            order = range(len(memory_value) - 1, -1, -1)
        else:
            order = range(0, len(memory_value))
        for index in order:
            reg = (reg << 8) | memory_value[index]

        reg &= ~self.bit_mask
        reg |= value << self.start_bit
        mem_value = reg.to_bytes(self.length, "little" if self.lsb_first else "big")

        try:
            obj._i2c.writeto_mem(obj._address, self.register, mem_value)
        except OSError as exc:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self.register) from exc


class RegisterStruct:
    """Descriptor for reading and writing structured I2C register data."""

    def __init__(self, register_address: int, form: str) -> None:
        if not isinstance(register_address, int):
            raise ValueError("register_address must be int")
        if not isinstance(form, str):
            raise ValueError("form must be str")
        if register_address < 0 or register_address > 0xFF:
            raise ValueError("register_address must be in range 0..255")
        if not form:
            raise ValueError("form must not be empty")

        self.format = form
        self.register = register_address
        self.length = struct.calcsize(form)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")

        try:
            raw = obj._i2c.readfrom_mem(obj._address, self.register, self.length)
        except OSError as exc:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self.register) from exc

        value = struct.unpack(self.format, raw)
        if len(value) == 1:
            return value[0]
        return value

    def __set__(self, obj, value) -> None:
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if isinstance(value, tuple):
            mem_value = struct.pack(self.format, *value)
        else:
            mem_value = struct.pack(self.format, value)

        try:
            obj._i2c.writeto_mem(obj._address, self.register, mem_value)
        except OSError as exc:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self.register) from exc


# ======================================== 初始化配置 ===========================================

# ========================================  主程序 ============================================
