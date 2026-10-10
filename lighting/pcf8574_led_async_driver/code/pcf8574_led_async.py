# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:10
# @Author  : 侯钧瀚
# @File    : pcf8574_led_async.py
# @Description : PCF8574 LED bar asynchronous driver
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# ======================================== 全局变量 ============================================
__version__ = "1.0.0"
__author__ = "侯钧瀚"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"
DEFAULT_ADDRESS = 0x20

# ======================================== 功能函数 ============================================
def _check_index(index: int) -> int:
    if not isinstance(index, int) or index < 0 or index > 7:
        raise ValueError("LED index must be from 0 to 7")
    return index

# ======================================== 自定义类 ============================================
class PCF8574Async:
    """PCF8574 单字节 I2C 端口访问的锁保护适配器。"""
    __slots__ = ("_i2c", "_address", "_port", "_lock", "_closed")

    def __init__(self, i2c: object, address: int = DEFAULT_ADDRESS) -> None:
        if not hasattr(i2c, "readfrom_into") or not hasattr(i2c, "writeto"):
            raise ValueError("i2c must provide readfrom_into and writeto")
        if not isinstance(address, int) or address < 0x20 or address > 0x27:
            raise ValueError("address must be from 0x20 to 0x27")
        self._i2c = i2c
        self._address = address
        self._port = bytearray(1)
        self._lock = asyncio.Lock()
        self._closed = False

    async def write_port_async(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("value must be an integer")
        async with self._lock:
            if self._closed:
                raise RuntimeError("PCF8574 is deinitialized")
            self._port[0] = value & 0xFF
            try:
                self._i2c.writeto(self._address, self._port)
            except OSError as exc:
                raise RuntimeError("PCF8574 I2C write failed") from exc

    async def read_port_async(self) -> int:
        async with self._lock:
            if self._closed:
                raise RuntimeError("PCF8574 is deinitialized")
            try:
                self._i2c.readfrom_into(self._address, self._port)
            except OSError as exc:
                raise RuntimeError("PCF8574 I2C read failed") from exc
            return self._port[0]

    async def write_pin_async(self, pin: int, value: bool) -> None:
        pin = _check_index(pin)
        async with self._lock:
            if self._closed:
                raise RuntimeError("PCF8574 is deinitialized")
            if value:
                self._port[0] |= 1 << pin
            else:
                self._port[0] &= ~(1 << pin)
            try:
                self._i2c.writeto(self._address, self._port)
            except OSError as exc:
                raise RuntimeError("PCF8574 I2C pin write failed") from exc

    def deinit(self) -> None:
        self._closed = True


class LEDBarAsync:
    """PCF8574 LED 条的短事务异步适配器。"""
    __slots__ = ("_pcf",)

    def __init__(self, pcf8574: PCF8574Async) -> None:
        if not isinstance(pcf8574, PCF8574Async):
            raise ValueError("pcf8574 must be a PCF8574Async instance")
        self._pcf = pcf8574

    async def set_led_async(self, index: int, value: bool) -> None:
        await self._pcf.write_pin_async(_check_index(index), bool(value))

    async def set_all_async(self, value: int) -> None:
        if not isinstance(value, int) or value < 0 or value > 0xFF:
            raise ValueError("value must be from 0 to 255")
        await self._pcf.write_port_async(value)

    async def display_level_async(self, level: int) -> None:
        if not isinstance(level, int) or level < 0 or level > 8:
            raise ValueError("level must be from 0 to 8")
        await self.set_all_async((1 << level) - 1 if level else 0)

    async def clear_async(self) -> None:
        await self.set_all_async(0)

    def deinit(self) -> None:
        self._pcf.deinit()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
