# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:20
# @Author  : mcauser
# @File    : ht16k33_async.py
# @Description : HT16K33 short-I2C asynchronous display adapter
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from ht16k33_seg import Seg7x4

# ======================================== 全局变量 ============================================
__version__ = "1.0.2"
__author__ = "mcauser"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class Seg7x4Async:
    """HT16K33 4 位数码管缓冲区和固定长度刷新适配器。"""
    __slots__ = ("_display", "_lock", "_closed")

    def __init__(self, i2c: object, address: int = 0x70) -> None:
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must provide writeto")
        if not isinstance(address, int) or address < 0 or address > 0x7F:
            raise ValueError("address must be a 7-bit I2C address")
        self._display = Seg7x4(i2c=i2c, address=address)
        self._lock = asyncio.Lock()
        self._closed = False

    def fill(self, value: bool) -> None:
        self._require_open()
        self._display.fill(value)

    def text(self, value: str) -> None:
        self._require_open()
        self._display.text(value)

    def hex(self, value: int) -> None:
        self._require_open()
        self._display.hex(value)

    def put(self, value: str, index: int = 0) -> None:
        self._require_open()
        self._display.put(value, index=index)

    async def show_async(self) -> None:
        async with self._lock:
            self._require_open()
            try:
                self._display.show()
            except OSError as exc:
                raise RuntimeError("HT16K33 display refresh failed") from exc

    async def brightness_async(self, value: int) -> None:
        async with self._lock:
            self._require_open()
            try:
                self._display.brightness(value)
            except OSError as exc:
                raise RuntimeError("HT16K33 brightness update failed") from exc

    def deinit(self) -> None:
        self._closed = True

    async def aclose(self) -> None:
        self.deinit()

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("display is deinitialized")

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
