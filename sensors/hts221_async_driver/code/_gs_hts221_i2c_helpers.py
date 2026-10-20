# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya (基于 Adafruit Industries 代码)
# @File    : i2c_helpers.py
# @Description : I2C 通信辅助类，提供位操作和寄存器结构体描述符
# @License : MIT

"""
I2C Communications helpers

Based on:
* adafruit_register.i2c_struct. Author(s): Scott Shawcroft
* adafruit_register.i2c_bits.  Author(s): Scott Shawcroft

MIT License
Copyright (c) 2016 Adafruit Industries
"""

import struct


class CBits:
    """
    位操作描述符类
    用于对 I2C 寄存器中的指定位段进行读取和写入操作
    ==========================================
    Bit-field descriptor class.
    Reads and writes specific bit fields within I2C registers.
    """

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width=1,
        lsb_first=True,
    ) -> None:
        # 计算位掩码
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
        # 从 I2C 设备读取寄存器值
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 将多字节值组装为整数
        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 提取目标位段
        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj, value: int) -> None:
        # 读取当前寄存器值
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 将多字节值组装为整数
        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]
        # 清除目标位段
        reg &= ~self.bit_mask

        # 设置新值到目标位段
        value <<= self.star_bit
        reg |= value
        # 将整数转换为字节数组
        reg = reg.to_bytes(self.lenght, "big")

        # 写入 I2C 设备
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    寄存器结构体描述符类
    使用 struct 格式字符串对 I2C 寄存器进行打包/解包读写操作
    ==========================================
    Register struct descriptor class.
    Reads and writes I2C registers using struct format strings for pack/unpack.
    """

    def __init__(self, register_address: int, form: str) -> None:
        self.format = form
        self.register = register_address
        # 计算 struct 格式所需的字节长度
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj,
        objtype=None,
    ):
        # 从 I2C 设备读取并解包数据
        if self.lenght <= 2:
            # 单值解包
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )[0]
        else:
            # 多值解包
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )
        return value

    def __set__(self, obj, value):
        # 将值打包为字节数组并写入 I2C 设备
        mem_value = value.to_bytes(self.lenght, "big")
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)
