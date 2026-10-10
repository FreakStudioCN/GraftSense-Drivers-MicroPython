# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : GraftSense Async Conversion
# @File    : apa102_async.py
# @Description : APA102/DotStar asynchronous frame scheduler
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from apa102 import DotStar

# ======================================== 全局变量 ============================================
BGR = DotStar.BGR

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class DotStarAsync:
    """锁保护 APA102 帧提交器；单次 SPI 写帧保持短同步操作。"""
    def __init__(self, spi, n, brightness=1.0, auto_write=False, pixel_order=BGR):
        self._driver = DotStar(spi, n, brightness=brightness, auto_write=False, pixel_order=pixel_order)
        self._auto_write = auto_write
        self._lock = asyncio.Lock()
        self._closed = False

    def __len__(self): return len(self._driver)
    def __getitem__(self, index): return self._driver[index]
    @property
    def brightness(self): return self._driver.brightness
    @brightness.setter
    def brightness(self, value): self._driver.brightness = value
    @property
    def auto_write(self): return self._auto_write
    @auto_write.setter
    def auto_write(self, value): self._auto_write = bool(value)
    def set_pixel(self, index, color): self._require_active(); self._driver[index] = color
    def fill(self, color): self._require_active(); self._driver.fill(color)
    async def set_pixel_async(self, index, color):
        self.set_pixel(index, color)
        if self._auto_write: await self.show_async()
    async def fill_async(self, color):
        self.fill(color)
        if self._auto_write: await self.show_async()
    async def show_async(self):
        self._require_active()
        async with self._lock:
            self._driver.show()
    async def color_wipe_async(self, color, delay_ms=100):
        for index in range(len(self)):
            self.set_pixel(index, color); await self.show_async(); await asyncio.sleep_ms(delay_ms)
        await self.fill_async((0, 0, 0))
    def deinit(self):
        if not self._closed: self._driver.deinit(); self._closed = True
    async def aclose(self):
        self.deinit()
    def _require_active(self):
        if self._closed: raise RuntimeError("DotStar is deinitialized")

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
