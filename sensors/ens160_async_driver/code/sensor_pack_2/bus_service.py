# MicroPython
# MIT license; Copyright (c) 2022 Roman Shevchik
# I2C/SPI 总线适配器模块

import math
from machine import I2C, SPI, Pin


def mpy_bl(value: int) -> int:
    """返回 value 所占位数，等效于 int.bit_length()（MicroPython 不支持该方法）。"""
    if 0 == value:
        return 0
    return 1 + int(math.log2(abs(value)))


class BusAdapter:
    """总线适配器基类，封装 I2C/SPI 读写操作。"""

    def __init__(self, bus):
        self.bus = bus

    def get_bus_type(self) -> type:
        return type(self.bus)

    def read_register(self, device_addr, reg_addr: int, bytes_count: int) -> bytes:
        raise NotImplementedError

    def write_register(self, device_addr, reg_addr: int, value, bytes_count: int, byte_order: str):
        raise NotImplementedError

    def read(self, device_addr, n_bytes: int) -> bytes:
        raise NotImplementedError

    def read_to_buf(self, device_addr, buf: bytearray) -> bytes:
        raise NotImplementedError

    def write(self, device_addr, buf: bytes):
        raise NotImplementedError

    def write_const(self, device_addr, val: int, count: int):
        """向总线发送 count 个值为 val 的字节，常用于填充显示缓冲区。"""
        if 0 == count:
            return
        bl = mpy_bl(val)
        if bl > 8:
            raise ValueError(f"Value must fit in 8 bits, got: {bl}")
        _max = min(16, count)
        b = bytearray([val] * _max)
        for _ in range(count // _max):
            self.write(device_addr, b)
        remainder = count % _max
        if remainder:
            self.write(device_addr, bytearray([val] * remainder))

    def read_buf_from_memory(self, device_addr, mem_addr, buf, address_size: int):
        raise NotImplementedError

    def write_buf_to_memory(self, device_addr, mem_addr, buf):
        raise NotImplementedError


class I2cAdapter(BusAdapter):
    """I2C 总线适配器。"""

    def __init__(self, bus: I2C):
        super().__init__(bus)

    def write_register(self, device_addr: int, reg_addr: int, value, bytes_count: int, byte_order: str):
        if isinstance(value, int):
            buf = value.to_bytes(bytes_count, byte_order)
        else:
            buf = value
        return self.bus.writeto_mem(device_addr, reg_addr, buf)

    def read_register(self, device_addr: int, reg_addr: int, bytes_count: int) -> bytes:
        return self.bus.readfrom_mem(device_addr, reg_addr, bytes_count)

    def read(self, device_addr: int, n_bytes: int) -> bytes:
        return self.bus.readfrom(device_addr, n_bytes)

    def read_to_buf(self, device_addr: int, buf: bytearray) -> bytes:
        self.bus.readfrom_into(device_addr, buf)
        return buf

    def write(self, device_addr: int, buf: bytes):
        return self.bus.writeto(device_addr, buf)

    def read_buf_from_memory(self, device_addr: int, mem_addr, buf, address_size: int = 1):
        self.bus.readfrom_mem_into(device_addr, mem_addr, buf)
        return buf

    def write_buf_to_memory(self, device_addr: int, mem_addr, buf):
        return self.bus.writeto_mem(device_addr, mem_addr, buf)


class SpiAdapter(BusAdapter):
    """SPI 总线适配器。data_mode 为数据/命令切换引脚（如 ILI9481 所需）。"""

    def __init__(self, bus: SPI, data_mode: Pin = None):
        super().__init__(bus)
        self.data_mode_pin = data_mode
        self.use_data_mode_pin = False
        self.data_packet = False
        self._address_index = 0
        self._prepare_before_send_ref = None

    @property
    def prepare_func(self):
        return self._prepare_before_send_ref

    @prepare_func.setter
    def prepare_func(self, value):
        self._prepare_before_send_ref = value

    def _call_prepare(self, buf: bytearray):
        ref = self._prepare_before_send_ref
        if ref is not None:
            ref(buf, self._address_index)

    def read(self, device_addr: Pin, n_bytes: int) -> bytes:
        try:
            device_addr.value(0)
            return self.bus.read(n_bytes)
        finally:
            device_addr.value(1)

    def read_to_buf(self, device_addr: Pin, buf) -> bytes:
        try:
            device_addr.value(0)
            self.bus.readinto(buf, 0x00)
            return buf
        finally:
            device_addr.value(1)

    def write(self, device_addr: Pin, buf: bytes):
        try:
            device_addr.value(0)
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write(buf)
        finally:
            device_addr.value(1)

    def write_and_read(self, device_addr: Pin, wr_buf: bytes, rd_buf: bytes):
        try:
            device_addr.value(0)
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write_readinto(wr_buf, rd_buf)
        finally:
            device_addr.value(1)

    def read_buf_from_memory(self, device_addr: Pin, mem_addr, buf, address_size: int):
        try:
            device_addr.value(0)
            raise NotImplementedError
        finally:
            device_addr.value(1)

    def write_buf_to_memory(self, device_addr: Pin, mem_addr, buf):
        try:
            device_addr.value(0)
            self._call_prepare(buf)
            raise NotImplementedError
        finally:
            device_addr.value(1)
