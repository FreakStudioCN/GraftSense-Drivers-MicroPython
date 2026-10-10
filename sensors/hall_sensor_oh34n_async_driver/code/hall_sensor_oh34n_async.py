# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : 缪贵成
# @File    : hall_sensor_oh34n_async.py
# @Description : OH34N asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class HallSensorOH34NAsync:
    """OH34N bridge with a preallocated ISR event flag."""

    def __init__(self, pin, callback=None):
        self._pin = Pin(pin, Pin.IN)
        self._callback = callback
        self._pending = False
        self._running = False
        self._irq = None
        self._task = None

    def read(self):
        return bool(self._pin.value())

    def set_callback(self, callback):
        self._callback = callback

    def _irq_handler(self, pin):
        self._pending = True

    async def enable_async(self, poll_ms=5):
        if self._running:
            return
        self._running = True
        self._irq = self._pin.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self._irq_handler,
        )
        self._task = asyncio.create_task(self._dispatch(poll_ms))

    async def _dispatch(self, poll_ms):
        while self._running:
            if self._pending:
                self._pending = False
                if self._callback is not None:
                    self._callback()
            await asyncio.sleep_ms(poll_ms)

    async def aclose(self):
        self._running = False
        self._pin.irq(handler=None)
        self._irq = None
        if self._task is not None:
            self._task.cancel()
            self._task = None

    def disable(self):
        self._running = False
        self._pin.irq(handler=None)
        self._irq = None

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
