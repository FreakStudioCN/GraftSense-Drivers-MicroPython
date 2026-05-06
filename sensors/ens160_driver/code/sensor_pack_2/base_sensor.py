# MicroPython
# MIT license; Copyright (c) 2022 Roman Shevchik
# 传感器基类与接口定义

import struct
import micropython
from sensor_pack_2 import bus_service
from machine import Pin


@micropython.native
def check_value(value, valid_range, error_msg):
    if value is None:
        return value
    if value not in valid_range:
        raise ValueError(error_msg)
    return value


def get_error_str(val_name: str, val: int, rng) -> str:
    if isinstance(rng, range):
        return f"参数 {val_name} 值 {val} 超出范围 [{rng.start}..{rng.stop - 1}]!"
    return f"参数 {val_name} 值 {val} 超出范围: {rng}!"


def all_none(*args):
    for element in args:
        if element is not None:
            return False
    return True


class Device:
    """传感器基类。big_byte_order=True 表示寄存器字节序为大端，否则为小端。"""

    def __init__(self, adapter: bus_service.BusAdapter, address, big_byte_order: bool):
        self.adapter = adapter
        self.address = address
        self.big_byte_order = big_byte_order
        self.msb_first = True

    def _get_byteorder_as_str(self) -> tuple:
        if self.is_big_byteorder():
            return 'big', '>'
        return 'little', '<'

    def pack(self, fmt_char: str, *values) -> bytes:
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        return struct.pack(bo + fmt_char, values)

    def unpack(self, fmt_char: str, source: bytes, redefine_byte_order: str = None) -> tuple:
        """解包从传感器读取的字节数组。fmt_char 参见 struct 文档。"""
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        if redefine_byte_order is not None:
            bo = redefine_byte_order[0]
        return struct.unpack(bo + fmt_char, source)

    @micropython.native
    def is_big_byteorder(self) -> bool:
        return self.big_byte_order


class DeviceEx(Device):
    """传感器扩展基类，封装寄存器读写方法。"""

    def read_reg(self, reg_addr: int, bytes_count=2) -> bytes:
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def write_reg(self, reg_addr: int, value, bytes_count) -> int:
        byte_order = self._get_byteorder_as_str()[0]
        return self.adapter.write_register(self.address, reg_addr, value, bytes_count, byte_order)

    def read_reg_16(self, address: int, signed: bool = False) -> int:
        return self.unpack("h" if signed else "H", self.read_reg(address, 2))[0]

    def write_reg_16(self, address: int, value: int):
        self.write_reg(address, value, 2)

    def read(self, n_bytes: int) -> bytes:
        return self.adapter.read(self.address, n_bytes)

    def read_to_buf(self, buf) -> bytes:
        return self.adapter.read_to_buf(self.address, buf)

    def write(self, buf: bytes):
        return self.adapter.write(self.address, buf)

    def read_buf_from_mem(self, address: int, buf, address_size: int = 1):
        return self.adapter.read_buf_from_memory(self.address, address, buf, address_size)

    def write_buf_to_mem(self, mem_addr, buf):
        return self.adapter.write_buf_to_memory(self.address, mem_addr, buf)


class BaseSensor(Device):
    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class BaseSensorEx(DeviceEx):
    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class Iterator:
    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError


class ITemperatureSensor:
    """温度传感器接口。"""

    def enable_temp_meas(self, enable: bool = True):
        raise NotImplementedError

    def get_temperature(self):
        raise NotImplementedError


class IPower:
    """功耗管理接口。level=0 为最大功耗，level=max 为最低功耗。"""

    def set_power_level(self, level=0) -> int:
        raise NotImplemented


class IDentifier:
    """设备标识接口。"""

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class IBaseSensorEx:
    """大多数传感器必须实现的通用接口。"""

    def get_conversion_cycle_time(self) -> int:
        raise NotImplemented

    def start_measurement(self):
        raise NotImplemented

    def get_measurement_value(self, value_index):
        raise NotImplemented

    def get_data_status(self, raw: bool = True):
        raise NotImplemented

    def is_single_shot_mode(self) -> bool:
        raise NotImplemented

    def is_continuously_mode(self) -> bool:
        raise NotImplemented
