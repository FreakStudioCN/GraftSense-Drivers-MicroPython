# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : 缪贵成
# @File    : flame_sensor_async.py
# @Description : Task-dispatched Flame sensor async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import Pin
import _gs_flame_flame_sensor as flame_sensor

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class FlameSensorAsync(flame_sensor.FlameSensor):
    """Event bridge that moves flame-pin reads and callbacks out of the ISR."""

    def __init__(self, analog_pin, digital_pin, callback=None):
        super().__init__(analog_pin=analog_pin, digital_pin=digital_pin, callback=None)
        self._async_callback = callback
        self._event_pending = False
        self._flame_detected = False
        self._running = False
        self._dispatch_task = None

    def _irq_handler(self, pin):
        self._event_pending = True

    async def _dispatch_loop(self, poll_ms=5):
        while self._running:
            if self._event_pending:
                self._event_pending = False
                self._flame_detected = bool(self._digital_pin.value())
                if self._async_callback:
                    self._async_callback()
            await asyncio.sleep_ms(poll_ms)

    async def enable_async(self, poll_ms=5):
        if self._irq is None:
            self._running = True
            self._dispatch_task = asyncio.create_task(self._dispatch_loop(poll_ms))
            self._irq = self._digital_pin.irq(
                trigger=Pin.IRQ_FALLING,
                handler=self._irq_handler,
            )

    async def disable_async(self):
        self.disable()

    async def is_flame_detected_async(self):
        return self.is_flame_detected()

    async def get_analog_value_async(self):
        return self.get_analog_value()

    async def get_voltage_async(self):
        return self.get_voltage()

    async def wait_for_flame_async(self, timeout_ms=10000, poll_ms=50):
        started = time.ticks_ms()
        while not self.is_flame_detected():
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                return False
            await asyncio.sleep_ms(poll_ms)
        return True

    async def aclose(self):
        self._running = False
        self.disable()
        if self._dispatch_task is not None:
            self._dispatch_task.cancel()
            self._dispatch_task = None
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ==============================================